import os
import json
import datetime
import websocket
from ast import literal_eval
from threading import Thread
from django.shortcuts import render
from django.http import JsonResponse
from projs.models import *
from users.models import UserProfile
from assets.models import Assets, ServerAssets
from utils.decorators import admin_auth, deploy_auth
from projs.utils.git_tools import GitTools
from projs.utils.svn_tools import SVNTools
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import permission_required


@permission_required('projs.add_project', raise_exception=True)
def proj_list(request):
    projects = Project.objects.select_related('project_admin').all().order_by('id')
    project_envs = Project.project_envs
    project_users = UserProfile.objects.all()
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


@admin_auth
def proj_config(request):
    projects = Project.objects.select_related('project_admin').all()
    repos = ProjectConfig.project_models
    server_assets = ServerAssets.objects.select_related('assets').all()
    pk = request.GET.get('id')

    if pk:
        return render(request, 'projs/config_detail.html', locals())
    else:
        return render(request, 'projs/proj_config.html', locals())


@permission_required('projs.deploy_project', raise_exception=True)
def config_list(request):
    user = request.user
    projects = user.proj_admin.all() | user.proj_member.all()
    configs = ProjectConfig.objects.select_related('project').all() if user.is_superuser else \
        [project.projectconfig for project in projects if
         hasattr(project, 'projectconfig') and project.project_env != 'prod']
    return render(request, 'projs/config_list.html', locals())


@deploy_auth
def deploy(request, pk):
    config = ProjectConfig.objects.select_related('project').get(id=pk)
    if request.method == 'GET':
        key = request.GET.get('key', None)
        mode = request.GET.get('mode', 'deploy')
        if config.repo == 'git':
            git_tool = GitTools(repo_url=config.repo_url, path=config.src_dir, env=config.project.project_env)
            if key:
                if key == 'model':
                    try:
                        git_tool.clone(prev_cmds=config.prev_deploy, username=config.repo_user,
                                       password=config.repo_password, git_port=config.git_port)
                        if config.repo_model == 'branch':
                            branches = git_tool.remote_branches
                            return JsonResponse({'code': 200, 'models': branches, 'msg': '获取成功！'})
                        elif config.repo_model == 'tag':
                            tags = git_tool.tags(versions=config.versions.split(','), mode=mode)
                            return JsonResponse({'code': 200, 'models': tags, 'msg': '获取成功！'})
                    except Exception as e:
                        return JsonResponse({'code': 500, 'msg': '获取失败：{}'.format(e)})
                elif key == 'commit':
                    try:
                        branch = request.GET.get('branch')
                        mode = request.GET.get('mode')
                        if request.GET.get('new_commit'):
                            git_tool.pull(branch)
                        commits = git_tool.get_commits(branch, versions=config.versions.split(','), mode=mode,
                                                       max_count=20)
                        return JsonResponse({'code': 200, 'data': commits, 'msg': '获取成功！'})
                    except Exception as e:
                        return JsonResponse({'code': 500, 'msg': '获取失败：{}'.format(e)})
            else:
                if os.path.exists(git_tool.proj_path):
                    local_branches = git_tool.local_branches
                    local_tags = tags = git_tool.tags(versions=config.versions.split(','), mode=mode)
                return render(request, 'projs/deploy.html', locals())

        elif config.repo == 'svn':
            svn_tool = SVNTools(repo_url=config.repo_url, path=config.src_dir, env=config.project.project_env,
                                username=config.repo_user, password=config.repo_password)
            if key:
                if key == 'model':
                    try:
                        if config.repo_model == 'branch':
                            branches = svn_tool.branches
                            return JsonResponse({'code': 200, 'models': branches, 'msg': '获取成功！'})
                        elif config.repo_model == 'tag':
                            tags = svn_tool.tags(versions=config.versions.split(','), mode=mode)
                            return JsonResponse({'code': 200, 'models': tags, 'msg': '获取成功！'})
                    except Exception as e:
                        return JsonResponse({'code': 500, 'msg': '获取失败：{}'.format(e)})
                elif key == 'commit':
                    branch = request.GET.get('branch')
                    try:
                        if branch == 'trunk':
                            commits = svn_tool.get_commits(versions=config.versions.split(','), mode=mode, limit=30)
                        else:
                            commits = svn_tool.get_commits(versions=config.versions.split(','), repo_model='branch',
                                                           model_name=branch, mode=mode, limit=30)
                        return JsonResponse({'code': 200, 'data': commits, 'msg': '获取成功！'})
                    except Exception as e:
                        return JsonResponse({'code': 500, 'msg': '获取失败：{}'.format(e)})
            else:
                return render(request, 'projs/deploy.html', locals())


@admin_auth
def deploy_log(request):
    pk = request.GET.get('pk')
    start_time = request.GET.get('startTime')
    end_time = request.GET.get('endTime')
    if pk:
        result = literal_eval(DeployLog.objects.get(id=pk).result)
        return JsonResponse({'code': 200, 'result': result})
    elif start_time and end_time:
        new_end_time = datetime.datetime.strptime(end_time, '%Y-%m-%d') + datetime.timedelta(1)
        end_time = new_end_time.strftime('%Y-%m-%d')
        try:
            records = []
            search_records = DeployLog.objects.select_related('project_config').select_related('deploy_user').filter(
                c_time__gt=start_time, c_time__lt=end_time)
            for search_record in search_records:
                record = {
                    'id': search_record.id,
                    'project_name': search_record.project_config.project.project_name,
                    'project_env': search_record.project_config.project.get_project_env_display(),
                    'd_type': search_record.get_d_type_display(),
                    'branch_tag': search_record.branch_tag,
                    'release_name': search_record.release_name[:7],
                    'release_desc': search_record.release_desc,
                    'deploy_user': search_record.deploy_user.username,
                    'c_time': search_record.c_time,
                }
                records.append(record)
            return JsonResponse({'code': 200, 'records': records})
        except Exception as e:
            return JsonResponse({'code': 500, 'error': '查询失败：{}'.format(e)})
    else:
        logs = DeployLog.objects.select_related('project_config').select_related('deploy_user').all()
        return render(request, 'projs/deploy_log.html', locals())


def check_log(request, pk):
    config = ProjectConfig.objects.prefetch_related('deploy_server').get(id=pk)
    server = config.deploy_server.first()
    host = server.assets.asset_management_ip
    port = server.port
    username = server.username
    password = server.password
    return render(request, 'projs/check_log.html',
                  {'host': host, 'port': port, 'username': username, 'password': password})


@csrf_exempt
def auto_deploy(request):
    if request.method == 'POST':
        token = request.META.get("HTTP_X_GITLAB_TOKEN")

        post_data = json.loads(request.body)

        try:
            config = ProjectConfig.objects.get(repo_url=post_data.get('repository').get('git_ssh_url'))
        except ProjectConfig.DoesNotExist:
            config = ProjectConfig.objects.get(repo_url=post_data.get('repository').get('git_http_url'))

        branch_name = post_data.get('ref').split('/')[-1]
        commit_id = post_data.get('commits')[0].get('id')

        ws_data = {'config_id': config.id, 'branch_tag': branch_name, 'commit': commit_id, 'rollback': False}

        ws_scheme = 'wss' if request.is_secure() else 'ws'

        def on_message(w, message):
            print('message=============', message)

        def on_error(w, error):
            pass

        def on_close(w):
            pass

        def on_open(w):
            w.send(json.dumps(ws_data, ensure_ascii=False))

        websocket.enableTrace(True)
        ws = websocket.WebSocketApp('{}://{}/ws/deploy/'.format(ws_scheme, request.META.get("HTTP_HOST")),
                                    on_message=on_message,
                                    on_error=on_error,
                                    on_close=on_close, )
        ws.on_open = on_open
        ws.run_forever()
        return JsonResponse({'code': 200, 'token': token, 'data': ws_data})
