from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from .models import Projects
import json
import hashlib
from django.conf import settings
from django.core.files import File
import os


def load_json_file(level):
    results = []
    with open('common/asvs.json') as f:
        data = json.load(f)
        for r in data['requirements']:
            bob = 'L{0}'.format(level)
            if r.get(bob):
                results.append(r)
    return results


def create_template(requirements, project):
    # delete all the levels out of the requirements as not needed in the template
    # for r in requirements:
    #     del r['levels']
    #     r['enabled'] = 0
    # build the template with project information and requirements
    data = {}
    data['project_owner'] = project['project_owner']
    data['project_name'] = project['project_name']
    data['project_id'] = project['id']
    data['project_description'] = project['project_description']
    data['project_created'] = project['project_created'].isoformat()
    data['project_level'] = project['project_level']
    data['requirements'] = requirements
    phash = (hashlib.md5('{0}{1}'.format(
        project['project_owner'], project['id']).encode('utf-8')).hexdigest())
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


@login_required
def project_all(request):
    projects = Projects.objects.filter(
        project_owner=request.user.username).values()
    return render(request, 'projects/manage.html', {'projects': projects})


@login_required
def project_add(request):
    if request.method == 'POST':
        # Create the database record
        project_name = request.POST.get('project_name')
        project_owner = request.user.username
        project_description = request.POST.get('project_description')
        project_level = request.POST.get('project_level')
        p = Projects(project_name=project_name, project_owner=project_owner,
                     project_description=project_description, project_level=project_level)
        p.save()
        # Build the template
        controls = load_json_file(project_level)
        project = Projects.objects.filter(
            project_owner=request.user.username, project_name=project_name).values()[0]
        create_template(controls, project)
        return redirect('projectsmanage')


@login_required
def project_delete(request, projectid):
    Projects.objects.filter(
        project_owner=request.user.username, pk=projectid).delete()
    phash = (hashlib.md5('{0}{1}'.format(
        request.user.username, projectid).encode('utf-8')).hexdigest())
    os.remove('storage/{0}.json'.format(phash))
    return redirect('projectsmanage')


@login_required
def project_view(request, projectid):
    phash = (hashlib.md5('{0}{1}'.format(
        request.user.username, projectid).encode('utf-8')).hexdigest())
    project = load_template(phash)
    if project['project_owner'] == request.user.username:
        percentage = calculate_completion(project['requirements'])
        return render(request, "projects/view.html", {'data': project['requirements'], 'project': project, 'percentage': percentage})


@login_required
def project_update(request):
    if request.method == 'POST':
        phash = (hashlib.md5('{0}{1}'.format(request.user.username, request.POST.get(
            'projectid')).encode('utf-8')).hexdigest())
        project = load_template(phash)
        for k, v in request.POST.items():
            if 'csrfmiddlewaretoken' in k or 'projectid' in k:
                pass
            else:
                for r in project['requirements']:
                    if r['Item'] in k:
                        if int(v) == 0:
                            r['enabled'] = 0
                        else:
                            r['enabled'] = 1
        update_template(phash, project)
        return redirect('projectsview', projectid=request.POST.get('projectid'))


@login_required
def project_download(request, projectid):
    phash = (hashlib.md5('{0}{1}'.format(
        request.user.username, projectid).encode('utf-8')).hexdigest())
    filename = 'storage/{0}.json'.format(phash)
    with open(filename, 'rb') as fh:
        response = HttpResponse(
            fh.read(), content_type="application/json")
        response['Content-Disposition'] = 'inline; filename=' + \
            os.path.basename(filename)
        return response
