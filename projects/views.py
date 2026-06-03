from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, render, redirect
from django.http import HttpResponse, JsonResponse
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.utils import timezone
from .models import AuditEvent, ProjectMember, ProjectRequirement, Projects, RequirementComment, RequirementEvidence
from .storage import (
    create_project_template,
    delete_project_template,
    load_project_template,
    save_project_template,
    template_path,
)
import json
import csv
import os
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Image
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase.pdfmetrics import registerFontFamily
from functools import wraps
import time
import datetime as dt
import textwrap
from user_agents import parse


def request_has_verified_2fa(request):
    if not request.user.is_authenticated or request.user.is_two_factor_enabled is not True:
        return False
    device_name = str(parse(request.META.get('HTTP_USER_AGENT', 'unknown')))
    return request.user.totpdevice_set.filter(
        confirmed=True,
        name=device_name,
    ).exists()


def two_factor_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request_has_verified_2fa(request):
            return redirect("authenticate_2fa")
        return view_func(request, *args, **kwargs)
    return login_required(wrapper)


def get_viewable_project(request, projectid):
    project = get_object_or_404(Projects, id=projectid)
    if not project.can_view(request.user):
        raise PermissionDenied
    return project


def get_manageable_project(request, projectid):
    project = get_object_or_404(Projects, id=projectid)
    if not project.can_manage(request.user):
        raise PermissionDenied
    return project


def get_editable_requirement(request, projectid, req_id):
    project = get_manageable_project(request, projectid)
    requirement = get_object_or_404(ProjectRequirement, project=project, req_id=req_id)
    return project, requirement


def add_chapter_name(requirement, categories):
    requirement['chapter_name'] = categories[int(requirement['chapter_id'][1:])]


def load_json_file(level):
    categories = {}
    with open(os.path.join(settings.BASE_DIR, 'common/category.json')) as j:
        categories_json = json.load(j)
        for c in categories_json['categories']:
            categories[c['id']] = c['title']
    results = []
    with open(os.path.join(settings.BASE_DIR, 'common/asvs.json')) as f:
        data = json.load(f)
        for r in data['requirements']:
            bob = 'level{0}'.format(level)
            if r.get(bob):
                add_chapter_name(r, categories)
                results.append(r)
    return results


def create_template(requirements, project):
    project_object = Projects.objects.get(id=project['id'])
    create_project_template(project_object, requirements)


def load_template(phash):
    with open(os.path.join(settings.BASE_DIR, 'storage/{0}.json'.format(phash)), 'r') as template:
        return json.load(template)


def update_template(phash, data):
    with open(os.path.join(settings.BASE_DIR, 'storage/{0}.json'.format(phash)), 'w') as template:
        json.dump(data, template, indent=2)


def calculate_completion(requirements):
    total = len(requirements)
    if total == 0:
        return {'total': 0, 'enabled': 0, 'percentage': '0.0'}
    enabled = 0
    for r in requirements:
        if r.get('enabled') and r['enabled'] > 0:
            enabled += 1
        else:
            pass
    percentage = enabled / total * 100
    return {'total': total, 'enabled': enabled, 'percentage': '{0:.1f}'.format(percentage)}


def project_metrics(project):
    requirements = project.requirements.all()
    total = requirements.count()
    complete = requirements.filter(status=ProjectRequirement.STATUS_COMPLETE).count()
    incomplete = requirements.filter(status=ProjectRequirement.STATUS_INCOMPLETE).count()
    review = requirements.filter(status=ProjectRequirement.STATUS_NEEDS_REVIEW).count()
    na = requirements.filter(status=ProjectRequirement.STATUS_NOT_APPLICABLE).count()
    percentage = complete / total * 100 if total else 0
    return {
        "total": total,
        "complete": complete,
        "incomplete": incomplete,
        "review": review,
        "na": na,
        "percentage": "{0:.1f}".format(percentage),
    }


def requirement_queryset_for_project(project, request):
    requirements = project.requirements.prefetch_related("evidence", "comments")
    status_filter = request.GET.get("status", "").strip()
    query = request.GET.get("q", "").strip()
    if status_filter:
        requirements = requirements.filter(status=status_filter)
    if query:
        requirements = requirements.filter(
            Q(req_id__icontains=query)
            | Q(req_description__icontains=query)
            | Q(chapter_name__icontains=query)
            | Q(section_name__icontains=query)
            | Q(cwe__icontains=query)
            | Q(nist__icontains=query)
            | Q(note__icontains=query)
        )
    return requirements


def grouped_requirements(requirements):
    groups = []
    by_chapter = {}
    for requirement in requirements:
        chapter = requirement.chapter_name or "Uncategorized"
        if chapter not in by_chapter:
            by_chapter[chapter] = {
                "title": chapter,
                "requirements": [],
                "total": 0,
                "complete": 0,
            }
            groups.append(by_chapter[chapter])
        group = by_chapter[chapter]
        group["requirements"].append(requirement)
        group["total"] += 1
        if requirement.status == ProjectRequirement.STATUS_COMPLETE:
            group["complete"] += 1
    for group in groups:
        group["percentage"] = "{0:.0f}".format(group["complete"] / group["total"] * 100) if group["total"] else "0"
    return groups


def update_project_members(project):
    ProjectMember.objects.update_or_create(
        project=project,
        username=project.project_owner,
        defaults={"role": ProjectMember.ROLE_OWNER},
    )
    for viewer in project.allowed_viewer_names():
        if viewer == project.project_owner:
            continue
        ProjectMember.objects.update_or_create(
            project=project,
            username=viewer,
            defaults={"role": ProjectMember.ROLE_VIEWER},
        )
    project.members.exclude(username__in=project.allowed_viewer_names()).exclude(username=project.project_owner).delete()


@two_factor_required
def project_all(request):

    projects = Projects.objects.visible_to(request.user)
    return render(request, 'projects/manage.html', {'projects': projects, 'user': request.user})


@two_factor_required
def project_add(request):
    if request.method == 'POST':
        # Create the database record
        project_name = request.POST.get('project_name', '').strip()
        project_owner = request.user.username
        project_description = request.POST.get('project_description', '').strip()
        project_level = request.POST.get('project_level', '1')
        if project_level not in ('1', '2', '3') or not project_name:
            return redirect('projectsmanage')
        p = Projects(project_name=project_name, project_owner=project_owner,
                     project_description=project_description, project_level=project_level)
        p.set_allowed_viewers(project_owner)
        p.save()
        update_project_members(p)
        # Build the template
        controls = load_json_file(project_level)
        create_project_template(p, controls)
        AuditEvent.objects.create(project=p, actor=request.user.username, action="project.created", detail=project_name)
        return redirect('projectsmanage')
    return redirect('projectsmanage')


@two_factor_required
def project_delete(request, projectid):
    p = get_manageable_project(request, projectid)
    delete_project_template(p)
    p.delete()
    return redirect('projectsmanage')


def get_chapter_styles():
    category_styles = {}
    with open(os.path.join(settings.BASE_DIR, 'common/category_styles.json')) as f:
        categories_json = json.load(f)
        for c in categories_json.get('categories'):
            category_styles[c.get('title')] = c.get('style')

    return category_styles


@two_factor_required
def project_view(request, projectid):
    p = get_viewable_project(request, projectid)
    project = load_project_template(p)
    project['project_created']=  add_one_hour(time.strftime("%m/%d/%Y %H:%M:%S",time.strptime(project['project_created'][:19], "%Y-%m-%dT%H:%M:%S")))
    styles = get_chapter_styles()
    requirements = requirement_queryset_for_project(p, request)

    return render(request, "projects/view.html", {
        'data': project['requirements'],
        'project': project,
        'percentage': calculate_completion(project['requirements']),
        'metrics': project_metrics(p),
        'groups': grouped_requirements(requirements),
        'styles': styles,
        'can_manage': p.can_manage(request.user),
        'status_choices': ProjectRequirement.STATUS_CHOICES,
        'active_status': request.GET.get("status", ""),
        'query': request.GET.get("q", ""),
        'audit_events': p.audit_events.select_related("requirement")[:8],
    })


@two_factor_required
def project_update(request):
    if request.method == 'POST':
        p = get_manageable_project(request, request.POST.get('projectid'))
        project = load_project_template(p)
        for r in project['requirements']:
            req_id = r['req_id']
            r['enabled'] = 1 if request.POST.get(req_id + 'status') == ProjectRequirement.STATUS_COMPLETE else 0
            r['disabled'] = 1 if request.POST.get(req_id + 'status') == ProjectRequirement.STATUS_INCOMPLETE else 0
            r['status'] = request.POST.get(req_id + 'status', ProjectRequirement.STATUS_NOT_APPLICABLE)
            if r['status'] == ProjectRequirement.STATUS_NOT_APPLICABLE:
                r['enabled'] = 0
                r['disabled'] = 0
            r['note'] = request.POST.get(req_id + 'note', '')[:5000]
        save_project_template(p, project)
        AuditEvent.objects.create(project=p, actor=request.user.username, action="project.bulk_updated", detail="")
        return redirect('projectsview', projectid=request.POST.get('projectid'))
    return redirect('projectsmanage')


@two_factor_required
def project_requirement_update(request, projectid, req_id):
    if request.method != "POST":
        return JsonResponse({"error": "POST required"}, status=405)
    project, requirement = get_editable_requirement(request, projectid, req_id)
    previous_status = requirement.status
    previous_note = requirement.note
    status_value = request.POST.get("status", requirement.status)
    if status_value not in dict(ProjectRequirement.STATUS_CHOICES):
        return JsonResponse({"error": "Invalid status"}, status=400)
    requirement.status = status_value
    requirement.note = request.POST.get("note", requirement.note)[:5000]
    if status_value in (ProjectRequirement.STATUS_COMPLETE, ProjectRequirement.STATUS_NEEDS_REVIEW):
        requirement.mark_reviewed(request.user.username)
    requirement.save()
    save_project_template(project, load_project_template(project))
    if previous_status != requirement.status or previous_note != requirement.note:
        AuditEvent.objects.create(
            project=project,
            requirement=requirement,
            actor=request.user.username,
            action="requirement.updated",
            detail="{0}: {1} -> {2}".format(requirement.req_id, previous_status, requirement.status),
        )
    return JsonResponse({
        "ok": True,
        "req_id": requirement.req_id,
        "status": requirement.status,
        "metrics": project_metrics(project),
        "updated_at": timezone.localtime(requirement.updated_at).strftime("%Y-%m-%d %H:%M"),
    })


@two_factor_required
def project_requirement_evidence_add(request, projectid, req_id):
    if request.method != "POST":
        return redirect('projectsview', projectid=projectid)
    project, requirement = get_editable_requirement(request, projectid, req_id)
    title = request.POST.get("title", "").strip()
    if title:
        RequirementEvidence.objects.create(
            requirement=requirement,
            title=title[:200],
            url=request.POST.get("url", "").strip(),
            notes=request.POST.get("notes", "").strip(),
            created_by=request.user.username,
        )
        AuditEvent.objects.create(project=project, requirement=requirement, actor=request.user.username, action="evidence.added", detail=title[:200])
    return redirect('projectsview', projectid=projectid)


@two_factor_required
def project_requirement_comment_add(request, projectid, req_id):
    if request.method != "POST":
        return redirect('projectsview', projectid=projectid)
    project, requirement = get_editable_requirement(request, projectid, req_id)
    body = request.POST.get("body", "").strip()
    if body:
        RequirementComment.objects.create(
            requirement=requirement,
            body=body[:5000],
            created_by=request.user.username,
        )
        AuditEvent.objects.create(project=project, requirement=requirement, actor=request.user.username, action="comment.added", detail=requirement.req_id)
    return redirect('projectsview', projectid=projectid)


@two_factor_required
def project_download(request, projectid):
    p = get_viewable_project(request, projectid)
    filename = template_path(p)
    with open(filename, 'rb') as fh:
        response = HttpResponse(
            fh.read(), content_type="application/json")
        response['Content-Disposition'] = 'inline; filename=' + \
            os.path.basename(filename)
        return response


@two_factor_required
def project_download_csv(request, projectid):
    p = get_viewable_project(request, projectid)
    response = HttpResponse(content_type="text/csv")
    response['Content-Disposition'] = 'attachment; filename="asvs-project-{0}.csv"'.format(p.id)
    writer = csv.writer(response)
    writer.writerow(["Requirement", "Chapter", "Section", "Status", "CWE", "NIST", "Note", "Evidence", "Comments"])
    for requirement in p.requirements.prefetch_related("evidence", "comments"):
        writer.writerow([
            requirement.req_id,
            requirement.chapter_name,
            requirement.section_name,
            requirement.get_status_display(),
            requirement.cwe,
            requirement.nist,
            requirement.note,
            requirement.evidence.count(),
            requirement.comments.count(),
        ])
    return response


@two_factor_required
def generate_pdf(request, projectid):
    p = get_viewable_project(request, projectid)
    project = load_project_template(p)
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="ProjectReport.pdf"'
    pdfmetrics.registerFont(TTFont('SantanderTextW05-Regular', os.path.join(settings.BASE_DIR, "static/fonts/SantanderText-Regular.ttf")))
    pdfmetrics.registerFont(TTFont('SantanderTextW05-Bold', os.path.join(settings.BASE_DIR, "static/fonts/SantanderText-Bold.ttf")))
    buffer = BytesIO()
    p = canvas.Canvas(buffer)
    data = [[],[],[],[],[],['PROJECT REPORT']] #First eements to give a space for the logo image
    data.append([" "])
    # Create the PDF object, using the BytesIO object as its "file."
    data.append(["•Project Owner:"]) 
    data.append(["   "+str(project['project_owner'])])
    data.append(["•Project Name:"])
    data.append(["   "+str(project['project_name'])])
    data.append(["•Project ID:"])
    data.append(["   "+str(project['project_id'])])
    data.append(["•Project Description:"])
    data.append(["   "+str(project['project_description'])])
    data.append(["•Project Created:"])
    data.append(["   "+str(add_one_hour(time.strftime("%m/%d/%Y %H:%M:%S",time.strptime(project['project_created'][:19], "%Y-%m-%dT%H:%M:%S"))))])
    data.append(["•Project Level:"])
    data.append(["   "+str(project['project_level'])])
    data.append([" "])
    data.append(["COMPLETION"])
    data.append([str(calculate_completion(project['requirements'])['percentage'])+"%"])
    data.append([str(calculate_completion(project['requirements'])['enabled'])+"/"+str(calculate_completion(project['requirements'])['total'])])  
    data.append([" "])
    data.append(["Requirements:"])
    data.append([" "])
    data.append([" "])
    for r in project['requirements']:   
        data.append([r['chapter_name']+":"])
        data.append([" "])
        split_description = chunkstring("("+r['req_id']+") "+r['req_description'], 123)
        for sd in split_description:
            data.append([sd])
        if r.get('enabled') and r['enabled'] > 0:
            data.append([" "])
            data.append(["Complete"])
            if (len(r.get('note', ''))>0):
                data.append(['"'+str(r.get('note', ''))+'"'])
            data.append([" "])

        elif r.get('disabled') and r['disabled'] > 0:
            data.append([" "])
            data.append(["Incomplete"])
            if (len(r.get('note', ''))>0):
                data.append(['"'+str(r.get('note', ''))+'"'])
            data.append([" "])
        else:
            data.append([" "])  
            data.append(["N/A"])
            if (len(r.get('note', ''))>0):
                data.append(['"'+str(r.get('note', ''))+'"'])
            data.append([" "])   

    if len(data) >= 40:
        pagenumber=0
        for x in range(len(data)+1):
            if (((x % 40 == 0) and (x > 0)) or x == len(data)):
                
                smalldata = data[x-40:x]
                width = 800
                height = 200
                x = 20
                y = 90
                canvasBackground(p,"#E3FFFA")
                if pagenumber==0:
                    detailsBackground(p,"#D3D3D3")
                    p.drawImage(os.path.join(settings.BASE_DIR, 'static/img/logoicon3.jpg'),227.5,730,width = 100, height = 100)

                p.drawImage(os.path.join(settings.BASE_DIR, 'static/img/logoicon3.jpg'),530,40,width = 40, height =40)
                table_style =  TableStyle([('FONTNAME', (0,0), (0,-1), 'SantanderTextW05-Regular')])
                for row, values, in enumerate(smalldata):
                    for column, value in enumerate(values):
                        if (value=="PROJECT REPORT" or value=="Requirements:" or value=="•Project Owner:" or value=="•Project Name:" or value=="•Project ID:" or value=="•Project Description:" or value=="•Project Created:" or value=="•Project Level:"or value=="COMPLETION"):
                            table_style.add('FONTNAME', (column, row), (column, row), 'SantanderTextW05-Bold')
                        if (value=="COMPLETION" or value=="PROJECT REPORT"):
                            table_style.add('ALIGN', (column, row), (column, row), "CENTRE")   
                            table_style.add('ALIGN', (column, row+1), (column, row+1), "CENTRE") 
                            table_style.add('SIZE', (column, row), (column, row), 12) 
                            if (value=="COMPLETION"):
                                table_style.add('ALIGN', (column, row+2), (column, row+2), "CENTRE")  
                        if value == "Complete":
                            table_style.add('TEXTCOLOR', (column, row), (column, row), "#49b675") 
                        if value == "Incomplete":
                            table_style.add('TEXTCOLOR', (column, row), (column, row), "#e71837")
                        if value == "N/A":
                            table_style.add('TEXTCOLOR', (column, row), (column, row), "#0e4bef")    
                        if value.startswith("Architecture"):
                            table_style.add('BACKGROUND', (column, row), (column, row), "#F6C2AE")
                        if value.startswith("Authentication"):
                            table_style.add('BACKGROUND', (column, row), (column, row), "#AEF6EE") 
                        if value.startswith("Session"):
                            table_style.add('BACKGROUND', (column, row), (column, row), "#AECEF6")    
                        if value.startswith("Access"):
                            table_style.add('BACKGROUND', (column, row), (column, row), "#F5F6AE") 
                        if value.startswith("Validation"):
                            table_style.add('BACKGROUND', (column, row), (column, row), "#97E995")
                        if value.startswith("Cryptography") or value.startswith("Stored Cryptography"):
                            table_style.add('BACKGROUND', (column, row), (column, row), "#7CC4A5")
                        if value.startswith("Error"):
                            table_style.add('BACKGROUND', (column, row), (column, row), "#FF8282")
                        if value.startswith("Data"):
                            table_style.add('BACKGROUND', (column, row), (column, row), "#C290BA")
                        if value.startswith("Communications"):
                            table_style.add('BACKGROUND', (column, row), (column, row), "#6986A0") 
                        if value.startswith("Malicious"):
                            table_style.add('BACKGROUND', (column, row), (column, row), "#AFBA7F")  
                        if value.startswith("BusLogic") or value.startswith("Business Logic"):
                            table_style.add('BACKGROUND', (column, row), (column, row), "#FFB962")  
                        if value.startswith("Files") or value.startswith("File"):
                            table_style.add('BACKGROUND', (column, row), (column, row), "#73E2D7") 
                        if value.startswith("API"):
                            table_style.add('BACKGROUND', (column, row), (column, row), "#80DAAD") 
                        if value.startswith("Configuration"):
                            table_style.add('BACKGROUND', (column, row), (column, row), "#CD0C2E")     

                f = Table(smalldata,style=table_style)
                f.wrapOn(p, width, height)
                f.drawOn(p, x, y)               
                p.showPage()
                pagenumber=pagenumber+1

    else:
        width = 800
        height = 200
        x = 20
        y = 767-17*len(data)
        canvasBackground(p,"#E3FFFA")
        detailsBackground(p,"#D3D3D3")
        p.drawImage(os.path.join(settings.BASE_DIR, 'static/img/logoicon3.jpg'),530,40,width = 40, height =40)
        grid = [('FONTNAME', (0,0), (0,-1), 'SantanderTextW05-Regular')]
        f = Table(data,style=TableStyle(grid))
        f.wrapOn(p, width, height)
        f.drawOn(p, x, y)       
        p.showPage()

    p.save()

    # Get the value of the BytesIO buffer and write it to the response.
    pdf = buffer.getvalue()
    buffer.close()
    response.write(pdf)
    return response


def chunkstring(text, length):
    list_of_strings=textwrap.wrap(text, length)    
    return(list_of_strings)


@two_factor_required
def modify_allowed_users(request, projectid):
    p = get_manageable_project(request, projectid)
    if request.method == 'POST':
        p.set_allowed_viewers(request.POST.get('viewers', ''))
        p.save()
        update_project_members(p)
        project = load_project_template(p)
        project['project_allowed_viewers'] = p.project_allowed_viewers
        save_project_template(p, project)
        AuditEvent.objects.create(project=p, actor=request.user.username, action="members.updated", detail=p.project_allowed_viewers)
        return redirect('projectsmanage')
    return redirect('projectsview', projectid=projectid)

#Adjust UTC timestamp to "Europe/London" Timezone
def add_one_hour(time_string):
    the_time = dt.datetime.strptime(time_string, '%m/%d/%Y %H:%M:%S')
    new_time = the_time + dt.timedelta(hours=1)
    return new_time.strftime('%m/%d/%Y %H:%M:%S')

def canvasBackground(canvas,colour):
    canvas.setFillColor(colour)
    path = canvas.beginPath()
    path.moveTo(0*cm,0*cm)
    path.lineTo(0*cm,30*cm)
    path.lineTo(25*cm,30*cm)
    path.lineTo(25*cm,0*cm)
    canvas.drawPath(path,True,True)  

def detailsBackground(canvas,colour):
    canvas.setFillColor(colour)
    path = canvas.beginPath()
    path.moveTo(0.7*cm,16.5*cm)
    path.lineTo(0.7*cm,24*cm)
    path.lineTo(20*cm,24*cm)
    path.lineTo(20*cm,16.5*cm)
    path.lineTo(0.7*cm,16.5*cm)
    canvas.drawPath(path,True,True)     
