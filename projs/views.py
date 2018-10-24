from django.shortcuts import render
from projs.models import *
from users.models import UserProfile
from assets.models import Assets
from django.contrib.auth.decorators import permission_required


@permission_required('projs.add_project', raise_exception=True)
def proj_list(request):
    projects = Project.objects.select_related('project_admin').all()
    project_envs = Project.project_envs
    project_models = Project.project_models
    project_admins = UserProfile.objects.all()
    return render(request, 'projs/proj_list.html', locals())


@permission_required('projs.add_service', raise_exception=True)
def proj_org(request, pk):
    project_obj = Project.objects.select_related('project_admin').get(id=pk)
    services = Service.objects.select_related('project').filter(project=project_obj)
    assets = Assets.objects.all()
    return render(request, 'projs/proj_org.html', locals())


@permission_required('projs.add_service', raise_exception=True)
def org_chart(request, pk):
    project_obj = Project.objects.select_related('project_admin').get(id=pk)
    services = Service.objects.select_related('project').filter(project=project_obj)
    return render(request, 'projs/org_chart.html', locals())
