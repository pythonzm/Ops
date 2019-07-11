import datetime
import os
import json
import zipfile
import shutil
from django.shortcuts import render
from task.utils.gen_resource import GenResource
from django.http import JsonResponse, HttpResponse
from task.models import *
from assets.models import ServerAssets
from django.conf import settings
from django.contrib.auth.decorators import permission_required
from utils.decorators import admin_auth


@permission_required('task.add_ansiblemodulelog', raise_exception=True)
def get_inventory_hosts(request):
    group_ids = request.GET.getlist('hostGroup')
    print(group_ids, type(group_ids))
    hosts = GenResource().gen_host_dict(group_ids)
    return JsonResponse({'code': 200, 'hosts': hosts})


@permission_required('task.add_ansiblemodulelog', raise_exception=True)
def run_module(request):
    inventory = AnsibleInventory.objects.prefetch_related('ans_group_hosts')
    hosts = ServerAssets.objects.select_related('assets')
    remote_ip = request.META['REMOTE_ADDR']
    return render(request, 'task/run_module.html', locals())


@permission_required('task.add_ansibleplaybook', raise_exception=True)
def playbook_add(request):
    if request.method == 'POST':
        playbook_name = request.POST.get('playbook_name')
        playbook_content = request.POST.get('playbook_content')
        today = datetime.date.today()

        upload_path = 'playbook/{}/{}/{}'.format(str(today.year), str(today.month), str(today.day))

        file = upload_path + '/' + playbook_name

        try:
            playbook = AnsiblePlaybook.objects.create(
                playbook_name=playbook_name,
                playbook_file=file,
                playbook_user=request.user,
                playbook_desc=request.POST.get('playbook_desc'),
                playbook_content=playbook_content
            )

            file_path = os.path.join(settings.MEDIA_ROOT, upload_path)
            if not os.path.exists(file_path):
                os.makedirs(file_path)

            with open('{}/{}'.format(file_path, playbook_name), 'w') as f:
                f.write(playbook_content)

            return JsonResponse(
                {'code': 200, 'msg': '添加完成！', 'id': playbook.id, 'playbook_time': playbook.playbook_time})
        except Exception as e:
            return JsonResponse({'code': 500, 'msg': '添加失败！'.format(e)})


@permission_required('task.add_ansibleplaybook', raise_exception=True)
def playbook_upload(request):
    if request.method == 'POST':
        playbook_file = request.FILES.get('playbook_file')
        playbook_name = request.POST.get('playbook_name')
        if playbook_file:
            playbook = AnsiblePlaybook.objects.create(
                playbook_name=playbook_file.name,
                playbook_file=playbook_file,
                playbook_user=request.user,
            )

            playbook_content = ''
            with open(playbook.playbook_file.path, 'r') as f:
                for line in f.readlines():
                    playbook_content = playbook_content + line

            playbook.playbook_content = playbook_content
            playbook.save()
            return JsonResponse(
                {'code': 200, 'msg': '添加文件完成！'})
        elif playbook_name:
            playbook_desc = request.POST.get('playbook_desc')
            playbook_obj = AnsiblePlaybook.objects.select_related('playbook_user').get(playbook_name=playbook_name)
            playbook_obj.playbook_desc = playbook_desc
            playbook_obj.save()
            return JsonResponse(
                {'code': 200, 'msg': '上传文件完成！', 'playbook_time': playbook_obj.playbook_time, 'id': playbook_obj.id})


@permission_required('task.add_ansibleplaybook', raise_exception=True)
def playbook_list(request):
    playbooks = AnsiblePlaybook.objects.select_related('playbook_user').all()
    inventory = AnsibleInventory.objects.prefetch_related('ans_group_hosts')
    remote_ip = request.META['REMOTE_ADDR']
    return render(request, 'task/playbook_list.html', locals())


@permission_required('task.change_ansibleplaybook', raise_exception=True)
def playbook_info(request, pk):
    playbook = AnsiblePlaybook.objects.select_related('playbook_user').get(id=pk)
    if request.method == 'GET':
        playbook_data = {
            'playbook_name': playbook.playbook_name,
            'playbook_desc': playbook.playbook_desc,
            'playbook_content': playbook.playbook_content
        }
        return JsonResponse({'code': 200, 'data': playbook_data})
    elif request.method == 'POST':
        try:
            playbook_content = request.POST.get('playbook_content')
            file = playbook.playbook_file.path

            with open(file, 'w') as f:
                f.write(playbook_content)

            AnsiblePlaybook.objects.select_related('playbook_user').filter(id=pk).update(
                playbook_name=request.POST.get('playbook_name'),
                playbook_content=playbook_content,
                playbook_desc=request.POST.get('playbook_desc')
            )

            return JsonResponse({'code': 200, 'msg': '更新完成！'})
        except Exception as e:
            return JsonResponse({'code': 500, 'msg': '更新失败！{}'.format(e)})


@permission_required('task.add_ansibleplaybook', raise_exception=True)
def playbook_run(request, pk):
    playbook = AnsiblePlaybook.objects.select_related('playbook_user').get(id=pk)
    content = playbook.playbook_content
    return JsonResponse({'code': 200, 'content': content})


@permission_required('task.delete_ansibleplaybook', raise_exception=True)
def playbook_del(request, pk):
    if request.method == 'DELETE':
        try:
            playbook = AnsiblePlaybook.objects.get(id=pk)
            os.remove(playbook.playbook_file.path)
            playbook.delete()
            return JsonResponse({'code': 200, 'msg': '删除成功！'})
        except Exception as e:
            return JsonResponse({'code': 500, 'msg': '删除失败！{}'.format(e)})


def check_name(request):
    playbook_name = request.GET.get('playbook_name')
    role_name = request.GET.get('role_name')
    playbook = AnsiblePlaybook.objects.filter(playbook_name=playbook_name).exists()
    role = AnsibleRole.objects.filter(role_name=role_name).exists()
    if playbook or role:
        return JsonResponse({'code': 500, 'msg': '同名文件已存在！'})
    else:
        return JsonResponse({'code': 200})


@admin_auth
def run_log(request):
    if request.method == 'POST':
        ansible_logs = None
        start_time = request.POST.get('startTime')
        end_time = request.POST.get('endTime')
        new_end_time = datetime.datetime.strptime(end_time, '%Y-%m-%d') + datetime.timedelta(1)
        end_time = new_end_time.strftime('%Y-%m-%d')
        log_type = request.POST.get('logType')
        try:
            if log_type == 'module':
                records = []
                ansible_logs = AnsibleModuleLog.objects.filter(ans_datetime__gt=start_time, ans_datetime__lt=end_time)
                for ansible_log in ansible_logs:
                    record = {
                        'id': ansible_log.id,
                        'ans_user': ansible_log.ans_user.username,
                        'ans_remote_ip': ansible_log.ans_remote_ip,
                        'ans_module': ansible_log.ans_module,
                        'ans_args': ansible_log.ans_args,
                        'ans_server': ansible_log.ans_server,
                        'ans_result': ansible_log.ans_result,
                        'ans_datetime': ansible_log.ans_datetime,
                    }
                    records.append(record)
                return JsonResponse({'code': 200, 'records': records})
            elif log_type == 'playbook':
                records = []
                ansible_logs = AnsiblePlaybookLog.objects.filter(playbook_datetime__gt=start_time,
                                                                 playbook_datetime__lt=end_time)
                for ansible_log in ansible_logs:
                    record = {
                        'id': ansible_log.id,
                        'playbook_user': ansible_log.playbook_user.username,
                        'playbook_remote_ip': ansible_log.playbook_remote_ip,
                        'playbook_name': ansible_log.playbook_name,
                        'playbook_result': ansible_log.playbook_result,
                        'playbook_datetime': ansible_log.playbook_datetime,
                    }
                    records.append(record)
                return JsonResponse({'code': 200, 'records': records})
        except Exception as e:
            return JsonResponse({'code': 500, 'error': '查询失败：{}'.format(e)})
    elif request.method == 'GET':
        module_log_id = request.GET.get('module_log_id')
        playbook_log_id = request.GET.get('playbook_log_id')
        if module_log_id:
            module_log = AnsibleModuleLog.objects.get(id=module_log_id)
            result = eval(module_log.ans_result)
            return JsonResponse({'code': 200, 'data': result})
        elif playbook_log_id:
            playbook_log = AnsiblePlaybookLog.objects.get(id=playbook_log_id)
            result = eval(playbook_log.playbook_result)
            return JsonResponse({'code': 200, 'data': result})
        else:
            module_log_info = AnsibleModuleLog.objects.select_related('ans_user').all()
            playbook_log_info = AnsiblePlaybookLog.objects.select_related('playbook_user').all()
            return render(request, 'task/run_log.html', locals())


@permission_required('task.delete_ansiblemodulelog', raise_exception=True)
def module_log_del(request, pk):
    if request.method == 'DELETE':
        try:
            AnsibleModuleLog.objects.filter(id=pk).delete()
            return JsonResponse({'code': 200, 'msg': '删除成功！'})
        except Exception as e:
            return JsonResponse({'code': 500, 'msg': '删除失败！'.format(e)})


@permission_required('task.delete_ansibleplaybooklog', raise_exception=True)
def playbook_log_del(request, pk):
    if request.method == 'DELETE':
        try:
            AnsiblePlaybookLog.objects.filter(id=pk).delete()
            return JsonResponse({'code': 200, 'msg': '删除成功！'})
        except Exception as e:
            return JsonResponse({'code': 500, 'msg': '删除失败！'.format(e)})


@permission_required('task.add_ansibleinventory', raise_exception=True)
def gen_inventory(request):
    inventory = AnsibleInventory.objects.prefetch_related('ans_group_hosts')
    hosts = ServerAssets.objects.select_related('assets')
    return render(request, 'task/inventory.html', locals())


@admin_auth
def role_detail(request, pk):
    if request.method == 'POST':
        name = request.POST.get('name')
        p_name = request.POST.get('p_name')
        if name and p_name:
            nodes = []
            path_names = os.listdir(os.path.join(p_name, name))
            path_names.sort()
            for path_name in path_names:
                if not path_name.endswith('retry'):
                    node = {'name': path_name, 'p_name': p_name + '/' + name}
                    if os.path.isdir(os.path.join(p_name, name, path_name)):
                        node['isParent'] = True
                    else:
                        node['isParent'] = False
                    nodes.append(node)
            return HttpResponse(json.dumps(nodes))
        else:
            role_name = AnsibleRole.objects.get(id=pk).role_name
            node = {'name': role_name, 'isParent': True, 'p_name': settings.ANSIBLE_ROLE_PATH}
            return HttpResponse(json.dumps(node))
    else:
        return render(request, 'task/role_detail.html', locals())


@permission_required('task.add_ansiblerole', raise_exception=True)
def role_add(request):
    if request.method == 'GET':
        role_name = request.GET.get('role_name')
        role_desc = request.GET.get('role_desc')
        root_path = settings.ANSIBLE_ROLE_PATH

        AnsibleRole.objects.select_related('role_user').create(
            role_name=role_name,
            role_file='{}/{}'.format('roles', role_name),
            role_user=request.user,
            role_desc=role_desc
        )
        return render(request, 'task/role_add.html', locals())


@permission_required('task.add_ansiblerole', raise_exception=True)
def get_file_content(request):
    p_name = request.GET.get('p_name')
    name = request.GET.get('name')
    file = os.path.join(p_name, name)
    if os.path.exists(file):
        content = ''
        with open(file, 'r') as f:
            for line in f.readlines():
                content = content + line

        relative_path = p_name.split('{}/{}/'.format(settings.MEDIA_ROOT, 'roles'))[-1] + '/' + name
        return JsonResponse({'code': 200, 'content': content, 'relative_path': relative_path})
    else:
        return JsonResponse({'code': 500, 'msg': 'No such file or dictionary!'})


@permission_required('task.addansiblerole', raise_exception=True)
def role_list(request):
    if request.method == 'GET':
        inventory = AnsibleInventory.objects.prefetch_related('ans_group_hosts')
        roles = AnsibleRole.objects.select_related('role_user').all()
        return render(request, 'task/role_list.html', locals())
    elif request.method == 'POST':
        role_file = request.FILES.get('role_file')
        role_name = request.POST.get('role_name')
        if role_file:
            AnsibleRole.objects.create(
                role_name=role_file.name.split('.zip')[0],
                role_file=role_file,
                role_user=request.user,
            )
        elif role_name:
            role_obj = AnsibleRole.objects.select_related('role_user').get(role_name=role_name.split('.zip')[0])
            role_obj.role_desc = request.POST.get('role_desc')
            role_obj.save()

            z = zipfile.ZipFile(role_obj.role_file.path, 'r')

            try:
                z.extractall(path=settings.ANSIBLE_ROLE_PATH)
            finally:
                z.close()
                os.remove(role_obj.role_file.path)

        return JsonResponse({'code': 200, 'msg': '上传成功！'})


@permission_required('task.change_ansiblerole', raise_exception=True)
def role_edit(request):
    if request.method == 'POST':
        content = request.POST.get('content')
        relative_path = request.POST.get('relative_path')
        p_name = request.POST.get('p_name')
        name = request.POST.get('name')

        try:
            if relative_path:
                with open(os.path.join(settings.ANSIBLE_ROLE_PATH, relative_path), 'w') as f:
                    f.write(content)
                return JsonResponse({'code': 200, 'msg': '修改完成！'})
            elif p_name and name:
                if not os.path.exists(p_name):
                    os.makedirs(p_name)
                with open(os.path.join(p_name, name), 'w') as f:
                    f.write(content)
                return JsonResponse({'code': 200, 'msg': '保存完成！'})
        except Exception as e:
            return JsonResponse({'code': 500, 'msg': '操作失败！：{}'.format(e)})


@permission_required('task.delete_ansiblerole', raise_exception=True)
def role_del(request, pk):
    if request.method == 'DELETE':
        role = AnsibleRole.objects.get(id=pk)
        try:
            shutil.rmtree(os.path.join(settings.ANSIBLE_ROLE_PATH, role.role_name))
            return JsonResponse({'code': 200, 'msg': '删除成功！'})
        except Exception as e:
            return JsonResponse({'code': 500, 'msg': '删除失败！{}'.format(e)})
        finally:
            role.delete()


@permission_required('task.delete_ansiblerole', raise_exception=True)
def path_del(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        p_name = request.POST.get('p_name')
        path = os.path.join(p_name, name)
        try:
            if os.path.exists(path):
                if os.path.isdir(path):
                    shutil.rmtree(path)
                else:
                    os.remove(path)
            return JsonResponse({'code': 200, 'msg': '删除成功！'})
        except Exception as e:
            return JsonResponse({'code': 500, 'msg': '删除失败！{}'.format(e)})


@permission_required('task.add_ansiblerole', raise_exception=True)
def path_create(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        p_name = request.POST.get('p_name')
        is_parent = request.POST.get('isParent')
        new_name = request.POST.get('new_name')
        path = os.path.join(p_name, name)
        new_path = os.path.join(p_name, new_name)
        try:
            if not os.path.exists(path) and not os.path.exists(new_path):
                if is_parent == 'true':
                    os.makedirs(new_path)
                else:
                    open(new_path, 'w').close()
                return JsonResponse({'code': 200, 'msg': '添加成功！'})
            elif os.path.exists(path) and not os.path.exists(new_path):
                os.rename(path, new_path)
                return JsonResponse({'code': 200, 'msg': '修改成功！'})
        except Exception as e:
            return JsonResponse({'code': 500, 'msg': '操作失败！{}'.format(e)})
