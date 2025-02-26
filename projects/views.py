from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from .models import Projects
import json
import hashlib
from django.core.files import File
import os
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Image
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase.pdfmetrics import registerFontFamily
from django.contrib.auth.decorators import user_passes_test
from django.db.models import Q
import time
import datetime as dt
import textwrap


def is_2fa_authenticated(user):
    try:
        return user.is_authenticated and user.is_two_factor_enabled is True and len(user.totpdevice_set.all())>0
    except user.DoesNotExist:
        return False


def add_chapter_name(requirement, categories):
    requirement['chapter_name'] = categories[int(requirement['chapter_id'][1:])]


def load_json_file(level):
    categories = {}
    with open('common/category.json') as j:
        categories_json = json.load(j)
        for c in categories_json['categories']:
            categories[c['id']] = c['title']
    results = []
    with open('common/asvs.json') as f:
        data = json.load(f)
        for r in data['requirements']:
            bob = 'level{0}'.format(level)
            if r.get(bob):
                add_chapter_name(r, categories)
                results.append(r)
    return results


def create_template(requirements, project):
    # build the template with project information and requirements
    data = {}
    data['project_owner'] = project['project_owner']
    data['project_name'] = project['project_name']
    data['project_id'] = project['id']
    data['project_description'] = project['project_description']
    data['project_created'] = project['project_created'].isoformat()
    data['project_level'] = project['project_level']
    data['requirements'] = requirements
    data['project_allowed_viewers'] = project['project_owner']
    phash = (hashlib.sha3_256('{0}{1}'.format(
        project['project_name'], project['id']).encode('utf-8')).hexdigest())
    with open('storage/{0}.json'.format(phash), 'w') as output:
        project_file = File(output)
        json.dump(data, project_file, indent=2)
    project_file.close()
    return


def load_template(phash):
    with open('storage/{0}.json'.format(phash), 'r') as template:
        data = json.load(template)
        template.close()
        return data


def update_template(phash, data):
    with open('storage/{0}.json'.format(phash), 'w') as template:
        json.dump(data, template, indent=2)
    template.close()
    return


def calculate_completion(requirements):
    total = len(requirements)
    enabled = 0
    for r in requirements:
        if r.get('enabled') and r['enabled'] > 0:
            enabled += 1
        else:
            pass
    percentage = enabled / total * 100
    return {'total': total, 'enabled': enabled, 'percentage': '{0:.1f}'.format(percentage)}


@user_passes_test(is_2fa_authenticated)
def project_all(request):

    if is_2fa_authenticated(request.user):
        if request.user.is_superuser:
            projects = list(Projects.objects.all().values())
        else:
            projects = list(Projects.objects.filter(Q(project_owner__exact=request.user.username) | Q(
                project_allowed_viewers__contains=request.user.username)).values())
            if len(projects)>0:    
                for p in projects:
                    #This code was written to fix a problem with django not distinguishing uppercase and lowercase on .filter
                    if p['project_owner']!=request.user.username and request.user.username not in p['project_allowed_viewers']:
                        projects.remove(p) 
        return render(request, 'projects/manage.html', {'projects': projects, 'user': request.user})


@user_passes_test(is_2fa_authenticated)
def project_add(request):
    if request.method == 'POST':
        # Create the database record
        project_name = request.POST.get('project_name')
        project_owner = request.user.username
        project_description = request.POST.get('project_description')
        project_level = request.POST.get('project_level')
        p = Projects(project_name=project_name, project_owner=project_owner,
                     project_description=project_description, project_level=project_level, project_allowed_viewers=project_owner)
        p.save()
        # Build the template
        controls = load_json_file(project_level)
        project = Projects.objects.filter(
            project_owner=request.user.username, project_name=project_name).values()[0]
        create_template(controls, project)
        return redirect('projectsmanage')


@user_passes_test(is_2fa_authenticated)
def project_delete(request, projectid):
    p = Projects.objects.get(id=projectid)
    Projects.objects.filter(
    project_owner=request.user.username, pk=projectid).delete()
    phash = (hashlib.sha3_256('{0}{1}'.format(
        p.project_name, projectid).encode('utf-8')).hexdigest())
    os.remove('storage/{0}.json'.format(phash))
    p.delete()
    return redirect('projectsmanage')


def get_chapter_styles():
    category_styles = {}
    with open('common/category_styles.json') as f:
        categories_json = json.load(f)
        for c in categories_json.get('categories'):
            category_styles[c.get('title')] = c.get('style')

    return category_styles


@user_passes_test(is_2fa_authenticated)
def project_view(request, projectid):
    p = Projects.objects.get(id=projectid)

    phash = (hashlib.sha3_256('{0}{1}'.format(
        p.project_name, projectid).encode('utf-8')).hexdigest())   
    project = load_template(phash)
    allowed_users = project['project_allowed_viewers'].split(",")
    project['project_created']=  add_one_hour(time.strftime("%m/%d/%Y %H:%M:%S",time.strptime(project['project_created'][:19], "%Y-%m-%dT%H:%M:%S")))
    percentage = calculate_completion(project['requirements'])
    styles = get_chapter_styles()

    if project['project_owner'] == request.user.username or request.user.username in allowed_users:
        return render(request, "projects/view.html", {'data': project['requirements'], 'project': project, 'percentage': percentage, 'styles': styles})
    else:
        return redirect('projectsmanage')    


@user_passes_test(is_2fa_authenticated)
def project_update(request):
    p = Projects.objects.get(id=request.POST.get(
            'projectid'))
    if request.method == 'POST':
        
        phash = (hashlib.sha3_256('{0}{1}'.format(p.project_name, request.POST.get(
            'projectid')).encode('utf-8')).hexdigest())
        project = load_template(phash)
        for k, v in request.POST.items():
            if 'csrfmiddlewaretoken' in k or 'projectid' in k:
                pass
            else:
                for r in project['requirements']:
                    if request.POST.get(r['req_id']+'enabled') == "1":
                        r['enabled'] = 1
                    else:
                        r['enabled'] = 0
                    if request.POST.get(r['req_id']+'disabled') == "1":
                        r['disabled'] = 1
                    else:
                        r['disabled'] = 0
                    if request.POST.get(r['req_id']+'na') == "1":
                        r['enabled'] = 0
                        r['disabled'] = 0
                    r['note']= request.POST.get(r['req_id']+'note')   
        p.save()
        update_template(phash, project)
        return redirect('projectsview', projectid=request.POST.get('projectid'))


@user_passes_test(is_2fa_authenticated)
def project_download(request, projectid):
    p = Projects.objects.get(id=projectid)
    phash = (hashlib.sha3_256('{0}{1}'.format(
        p.project_name, projectid).encode('utf-8')).hexdigest())
    filename = 'storage/{0}.json'.format(phash)
    with open(filename, 'rb') as fh:
        response = HttpResponse(
            fh.read(), content_type="application/json")
        response['Content-Disposition'] = 'inline; filename=' + \
            os.path.basename(filename)
        return response


@user_passes_test(is_2fa_authenticated)
def generate_pdf(request, projectid):
    p = Projects.objects.get(id=projectid)
    phash = (hashlib.sha3_256('{0}{1}'.format(
        p.project_name, projectid).encode('utf-8')).hexdigest())
    project = load_template(phash)
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="ProjectReport.pdf"'
    pdfmetrics.registerFont(TTFont('SantanderTextW05-Regular', "./static/fonts/SantanderText-Regular.ttf"))
    pdfmetrics.registerFont(TTFont('SantanderTextW05-Bold', "./static/fonts/SantanderText-Bold.ttf"))
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
            if (len(r['note'])>0):
                data.append(['"'+str(r['note'])+'"'])
            data.append([" "])

        elif r.get('disabled') and r['disabled'] > 0:
            data.append([" "])
            data.append(["Incomplete"])
            if (len(r['note'])>0):
                data.append(['"'+str(r['note'])+'"'])
            data.append([" "])
        else:
            data.append([" "])  
            data.append(["N/A"])
            if (len(r['note'])>0):
                data.append(['"'+str(r['note'])+'"'])
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
                    p.drawImage('./static/img/logoicon3.jpg',227.5,730,width = 100, height = 100)
                
                p.drawImage('./static/img/logoicon3.jpg',530,40,width = 40, height =40)     
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
        p.drawImage('./static/img/logoicon3.jpg',530,40,width = 40, height =40)
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


def modify_allowed_users(request, projectid):
    p = Projects.objects.get(id=projectid)
    if request.method == 'POST':
        phash = (hashlib.sha3_256('{0}{1}'.format(
            p.project_name, projectid).encode('utf-8')).hexdigest())

        change = Projects.objects.get(id=projectid)
        change.project_allowed_viewers = request.POST.get('viewers')
        change.save()
        return redirect('projectsmanage')

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