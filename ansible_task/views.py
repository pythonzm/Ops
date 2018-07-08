from django.shortcuts import render
from ansible_task.utils.ansible_api_v2 import ANSRunner
from django.http import JsonResponse, HttpResponse
from django.core import serializers
from django.views.decorators.csrf import csrf_exempt
from ansible_task.models import AnsibleModuleLog
from utils.db.redis_ops import RedisOps
from Ops import settings


def run_module(request):
    if request.method == 'POST':
        redis_conn = RedisOps(settings.REDIS_HOST, settings.REDIS_PORT, settings.REDIS_DB)
        remote_ip = request.META['REMOTE_ADDR']
        host = request.POST.getlist('host')
        selected_module_name = request.POST.get('ansibleModel')
        custom_model_name = request.POST.get('customModel')
        module_name = selected_module_name if selected_module_name else custom_model_name
        module_args = request.POST.get('ansibleModelArgs')

        unique_key = '{}.{}.{}'.format(host, module_name, module_args)

        if redis_conn.exists(unique_key):
            return JsonResponse({'res': ['有相同的任务正在执行，请稍后再试']})
        else:
            try:
                redis_conn.set(unique_key, 1)
                ans = ANSRunner()
                ans.run_module(host_list=host, module_name=module_name, module_args=module_args)
                res = ans.get_model_result()
                AnsibleModuleLog.objects.create(
                    ans_user=str(request.user),
                    ans_remote_ip=remote_ip,
                    ans_module=module_name,
                    ans_args=module_args,
                    ans_server=','.join(host),
                    ans_result=res,
                )
                return JsonResponse({'res': res})
            except Exception as e:
                return JsonResponse({'res': ['任务执行失败：{}'.format(e)]})
            finally:
                redis_conn.delete(unique_key)
    group_names = ANSRunner().get_group_names()
    return render(request, 'ansible_task/run_model.html', locals())


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
    return render(request, 'ansible_task/run_log.html', locals())

