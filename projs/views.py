from django.shortcuts import render
from django.http import JsonResponse
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
    if request.method == 'GET':
        project_org = project_obj.project_org
        return render(request, 'projs/proj_org.html', locals())
    elif request.method == 'POST':
        try:
            data = request.POST.get('data')
            project_obj.project_org = data
            project_obj.save()
            return JsonResponse({'code': 200, 'msg': '保存成功！'})
        except Exception as e:
            return JsonResponse({'code': 500, 'msg': '保存失败！{}'.format(e)})


@permission_required('projs.add_service', raise_exception=True)
def org_chart(request, pk):
    project_obj = Project.objects.select_related('project_admin').get(id=pk)
    project_org = project_obj.project_org
    return render(request, 'projs/org_chart.html', locals())
