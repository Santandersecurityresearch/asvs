from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import Projects


# create a new project
# view projects
# delete projects


@login_required
def projects_all(request):
    projects = Projects.objects.filter(
        project_owner=request.user.username).values()
    return render(request, 'projects/view.html', {'projects': projects})


@login_required
def projects_add(request):
    if request.method == 'POST':
        project_name = request.POST.get('project_name')
        project_owner = request.user.username
        project_description = request.POST.get('project_description')
        project_level = request.POST.get('project_level')
        p = Projects(project_name=project_name, project_owner=project_owner,
                     project_description=project_description, project_level=project_level)
        p.save()
        return redirect('projectsall')
