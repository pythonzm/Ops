import datetime
import os
from django.shortcuts import render
from task.utils.ansible_api_v2 import ANSRunner
from django.http import JsonResponse, HttpResponseForbidden
from task.models import *
from assets.models import ServerAssets
from utils.db.redis_ops import RedisOps
from Ops import settings
from utils.crypt_pwd import CryptPwd
from django.contrib.auth.decorators import permission_required


def gen_resource(host_ids, group_ids=None):
    host_list = []
    for host_id in host_ids:
        host = {}
        host_obj = ServerAssets.objects.get(id=host_id)
        host['ip'] = host_obj.assets.asset_management_ip
        host['port'] = int(host_obj.port)
        host['username'] = host_obj.username
        host['password'] = CryptPwd().decrypt_pwd(host_obj.password)
        if host_obj.host_vars:
            host_vars = eval(host_obj.host_vars)
            for k, v in host_vars.items():
                host[k] = v
        host_list.append(host)
    if group_ids:
        resource = {}
        group_values = {}
        for group_id in group_ids:
            group_obj = AnsibleInventory.objects.get(id=group_id)
            group_values['hosts'] = host_list
            if group_obj.ans_group_vars:
                group_values['group_vars'] = eval(group_obj.ans_group_vars)
            resource[group_obj.ans_group_name] = group_values
    else:
        resource = host_list

    return resource


@permission_required('task.add_ansiblemodulelog', raise_exception=True)
def run_module(request):
    if request.method == 'POST':
        redis_conn = RedisOps(settings.REDIS_HOST, settings.REDIS_PORT, settings.REDIS_DB)
        remote_ip = request.META['REMOTE_ADDR']
        group_ids = request.POST.getlist('hostGroup')
        host_ids = request.POST.getlist('ans_group_hosts')
        if group_ids == ['custom'] or group_ids == ['all']:
            resource = gen_resource(host_ids)
        else:
            resource = gen_resource(host_ids, group_ids)

        host_list = [ServerAssets.objects.get(id=host_id).assets.asset_management_ip for host_id in host_ids]
        selected_module_name = request.POST.get('ansibleModule')
        custom_model_name = request.POST.get('customModule')
        module_name = selected_module_name if selected_module_name != 'custom' else custom_model_name
        module_args = request.POST.get('ansibleModuleArgs')

        unique_key = '{}.{}.{}'.format(host_ids, module_name, module_args)

        if redis_conn.exists(unique_key):
            return JsonResponse({'msg': ['有相同的任务正在执行，请稍后再试'], 'code': 403})
        else:
            try:
                redis_conn.set(unique_key, 1)
                ans = ANSRunner(resource)
                ans.run_module(host_list=host_list, module_name=module_name, module_args=module_args)
                res = ans.get_model_result()

                return JsonResponse({'code': 200, 'msg': res})
            except Exception as e:
                return JsonResponse({'code': 500, 'msg': ['任务执行失败：{}'.format(e)]})
            finally:
                redis_conn.delete(unique_key)
    inventory = AnsibleInventory.objects.prefetch_related('ans_group_hosts')
    hosts = ServerAssets.objects.select_related('assets')
    return render(request, 'task/run_module.html', locals())


@permission_required('task.add_ansibleplaybook', raise_exception=True)
def run_playbook_online(request):
    if request.method == 'POST':
        group_ids = request.POST.getlist('playbook_inventory')
        playbook_name = request.POST.get('playbook_name')
        playbook_content = request.POST.get('playbook_content')
        today = datetime.date.today()

        upload_path = 'playbook/{}/{}/{}'.format(str(today.year), str(today.month), str(today.day))

        file_path = os.path.join(settings.MEDIA_ROOT, upload_path)

        file = upload_path + '/' + playbook_name

        playbook = AnsiblePlaybook.objects.create(
            playbook_name=playbook_name,
            playbook_file=file,
            playbook_user=request.user,
            playbook_desc=request.POST.get('playbook_desc'),
            playbook_content=playbook_content
        )

        playbook.playbook_inventory.set(group_ids, clear=True)

        if not os.path.exists(file_path):
            os.makedirs(file_path)

        with open('{}/{}'.format(file_path, playbook_name), 'w') as f:
            f.write(playbook_content)

        try:
            res = get_playbook_res(group_ids, os.path.join(file_path, playbook_name))
            return JsonResponse({'code': 200, 'msg': res})
        except Exception as e:
            return JsonResponse({'code': 500, 'msg': ['playbook执行失败：{}'.format(e)]})

    elif request.method == 'GET':
        inventory = AnsibleInventory.objects.prefetch_related('ans_group_hosts')
        return render(request, 'task/run_playbook_online.html', locals())


@permission_required('task.add_ansibleplaybook', raise_exception=True)
def playbook_upload(request):
    if request.method == 'POST':
        playbook_inventory = request.POST.getlist('playbook_inventory')
        playbook_file = request.FILES.get('playbook_file')

        if playbook_file:
            playbook = AnsiblePlaybook.objects.create(
                playbook_name=playbook_file.name,
                playbook_file=playbook_file,
                playbook_user=request.user,
                playbook_desc=request.POST.get('playbook_desc')
            )

            playbook_content = ''
            with open(playbook.playbook_file.path, 'r') as f:
                for line in f.readlines():
                    playbook_content = playbook_content + line

            playbook.playbook_content = playbook_content
            playbook.save()
        elif playbook_inventory:
            playbook_name = request.POST.get('playbook_name')
            playbook_desc = request.POST.get('playbook_desc')
            playbook_obj = AnsiblePlaybook.objects.select_related('playbook_user').get(playbook_name=playbook_name)
            playbook_obj.playbook_desc = playbook_desc
            playbook_obj.playbook_inventory.set(playbook_inventory, clear=True)
            playbook_obj.save()
        return JsonResponse({'code': 200, 'msg': '上传成功！'})


@permission_required('task.add_ansibleplaybook', raise_exception=True)
def playbook_list(request):
    playbooks = AnsiblePlaybook.objects.select_related('playbook_user').prefetch_related('playbook_inventory').all()
    inventory = AnsibleInventory.objects.prefetch_related('ans_group_hosts')
    return render(request, 'task/playbook_list.html', locals())


@permission_required('task.change_ansibleplaybook', raise_exception=True)
def playbook_info(request, pk):
    playbook = AnsiblePlaybook.objects.select_related('playbook_user').prefetch_related('playbook_inventory').get(id=pk)
    if request.method == 'GET':
        inventory = AnsibleInventory.objects.prefetch_related('ans_group_hosts')

        playbook_inventory = playbook.playbook_inventory.all()
        group_ids = [ans_group.id for ans_group in playbook_inventory]
        inventory_hosts = []
        for group_id in group_ids:
            ans_hosts = AnsibleInventory.objects.prefetch_related('ans_group_hosts').get(
                id=group_id).ans_group_hosts.all()
            inventory_hosts.extend([ans_host for ans_host in ans_hosts])
        inventory_hosts = list(set(inventory_hosts))
        return render(request, 'task/playbook_info.html', locals())
    elif request.method == 'POST':
        try:
            playbook_content = request.POST.get('playbook_content')
            file = AnsiblePlaybook.objects.get(id=pk).playbook_file.path

            with open(file, 'w') as f:
                f.write(playbook_content)

            AnsiblePlaybook.objects.select_related('playbook_user').filter(id=pk).update(
                playbook_name=request.POST.get('playbook_name'),
                playbook_content=playbook_content,
                playbook_desc=request.POST.get('playbook_desc')
            )
            playbook.playbook_inventory.set(request.POST.getlist('playbook_inventory'), clear=True)

            return JsonResponse({'code': 200, 'msg': '更新完成！'})
        except Exception as e:
            return JsonResponse({'code': 500, 'msg': '更新失败！{}'.format(e)})


@permission_required('task.add_ansibleplaybook', raise_exception=True)
def playbook_run(request, pk):
    playbook = AnsiblePlaybook.objects.select_related('playbook_user').prefetch_related('playbook_inventory').get(
        id=pk)
    playbook_inventory = playbook.playbook_inventory.all()
    group_ids = [ans_group.id for ans_group in playbook_inventory]

    if request.method == 'GET':
        group_names = [ans_group.ans_group_name for ans_group in playbook_inventory]
        content = playbook.playbook_content
        return JsonResponse({'code': 200, 'inventory': group_names, 'content': content})
    elif request.method == 'POST':
        try:
            res = get_playbook_res(group_ids, playbook.playbook_file.path)
            return JsonResponse({'code': 200, 'msg': res})
        except Exception as e:
            return JsonResponse({'code': 500, 'msg': ['playbook执行失败：{}'.format(e)]})


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


def check_playbook_name(request):
    playbook_name = request.GET.get('playbook_name')
    playbook = AnsiblePlaybook.objects.filter(playbook_name=playbook_name).exists()
    if playbook:
        return JsonResponse({'code': 500, 'msg': '同名文件已存在！'})
    else:
        return JsonResponse({'code': 200})


def get_inventory_hosts(request):
    if request.method == 'POST':
        group_ids = []
        if request.POST.getlist('playbook_inventory'):
            group_ids = request.POST.getlist('playbook_inventory')
        elif request.POST.getlist('hostGroup'):
            group_ids = request.POST.getlist('hostGroup')

        hosts = []
        host_ids = []
        for group_id in group_ids:
            host_list = AnsibleInventory.objects.prefetch_related('ans_group_hosts').get(
                id=group_id).ans_group_hosts.all()
            host_id_list = [host.id for host in host_list]
            host_ips = [host.assets.asset_management_ip for host in host_list]
            hosts.extend(host_ips)
            host_ids.extend(host_id_list)

        hosts = list(set(hosts))
        host_ids = list(set(host_ids))
        return JsonResponse({'code': 200, 'host_ips': hosts, 'host_ids': host_ids})


def get_playbook_res(group_ids, playbook_file):
    host_ids = None
    for group_id in group_ids:
        inventory_obj = AnsibleInventory.objects.prefetch_related('ans_group_hosts').get(id=group_id)
        hosts = inventory_obj.ans_group_hosts.all()
        host_ids = [host.id for host in hosts]
    host_ids = list(set(host_ids))
    resource = gen_resource(host_ids, group_ids)

    ans = ANSRunner(resource)
    ans.run_playbook(playbook_file)
    res = ans.get_playbook_result()
    return res


@permission_required('task.add_ansiblemodulelog', raise_exception=True)
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
        if request.user.is_superuser:
            module_log_info = AnsibleModuleLog.objects.select_related('ans_user').all()
            playbook_log_info = AnsiblePlaybookLog.objects.select_related('playbook_user').all()
            return render(request, 'task/run_log.html', locals())
        else:
            return HttpResponseForbidden('<h1>403</h1>')


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
