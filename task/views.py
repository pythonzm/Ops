from django.shortcuts import render
from task.utils.ansible_api_v2 import ANSRunner
from django.http import JsonResponse, HttpResponse
from django.core import serializers
from django.views.decorators.csrf import csrf_exempt
from task.models import *
from assets.models import ServerAssets
from utils.db.redis_ops import RedisOps
from Ops import settings
from utils.crypt_pwd import CryptPwd


def gen_resource(host_ids, group_ids=None):
    host_list = []
    for host_id in host_ids:
        host = {}
        host_obj = ServerAssets.objects.get(id=host_id)
        host['ip'] = host_obj.assets.asset_management_ip
        host['port'] = host_obj.port
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

                return JsonResponse({'msg': res})
            except Exception as e:
                return JsonResponse({'msg': ['任务执行失败：{}'.format(e)]})
            finally:
                redis_conn.delete(unique_key)
    inventory = AnsibleInventory.objects.prefetch_related('ans_group_hosts')
    hosts = ServerAssets.objects.select_related('assets')
    return render(request, 'task/run_module.html', locals())


@csrf_exempt
def parse_group(request):
    if request.method == 'POST':
        hosts = []
        selected_groups = request.POST.getlist('hostGroup')
        group_dict = ANSRunner().get_group_dict()
        for group in selected_groups:
            if group == 'custom':
                hosts.extend(group_dict['all'])
            for groupname, host in group_dict.items():
                if groupname == group:
                    hosts.extend(group_dict[group])
        hosts = list(set(hosts))
        return JsonResponse({'hosts': hosts})


def run_log(request):
    if request.method == 'POST':
        ansible_logs = None
        start_time = request.POST.get('startTime')
        end_time = request.POST.get('endTime')
        log_type = request.POST.get('logType')
        try:
            if log_type == 'module':
                ansible_logs = AnsibleModuleLog.objects.filter(ans_datetime__gte=start_time, ans_datetime__lte=end_time)
            elif log_type == 'playbook':
                pass
            ansible_logs = serializers.serialize('json', ansible_logs)
            return HttpResponse(ansible_logs)
        except Exception as e:
            return JsonResponse({'error': '查询失败：{}'.format(e)})
    module_log_info = AnsibleModuleLog.objects.all()
    return render(request, 'task/run_log.html', locals())


def gen_inventory(request):
    inventory = AnsibleInventory.objects.prefetch_related('ans_group_hosts')
    hosts = ServerAssets.objects.select_related('assets')
    return render(request, 'task/inventory.html', locals())
