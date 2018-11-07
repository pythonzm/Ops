import datetime
from django.shortcuts import render
from task.utils.ansible_api_v2 import ANSRunner
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
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
                pass
        except Exception as e:
            return JsonResponse({'code': 500, 'error': '查询失败：{}'.format(e)})
    module_log_info = AnsibleModuleLog.objects.select_related('ans_user').all()
    return render(request, 'task/run_log.html', locals())


@permission_required('task.add_ansibleinventory', raise_exception=True)
def gen_inventory(request):
    inventory = AnsibleInventory.objects.prefetch_related('ans_group_hosts')
    hosts = ServerAssets.objects.select_related('assets')
    return render(request, 'task/inventory.html', locals())
