from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import render
from fort.models import *
from assets.models import ServerAssets
from django.contrib.auth.models import Group
from users.models import UserProfile
import datetime
from task.views import gen_resource
from task.utils.ansible_api_v2 import ANSRunner
from django.contrib.auth.decorators import permission_required


@permission_required('Ops.add_fortserver', raise_exception=True)
def fort_server(request):
    fort_servers = FortServer.objects.select_related('server')
    black_commands, created = FortBlackCommand.objects.get_or_create(id=1)
    fort_users = FortServerUser.objects.select_related('fort_server')
    if request.method == 'POST':
        try:
            new_black_commands = request.POST.get('black_commands')

            if fort_users.count() > 0:

                old_format_commands = format_commands(black_commands.black_commands)
                new_format_commands = format_commands(new_black_commands)

                for fort_server_obj in fort_servers:
                    sudo_users = [user.fort_username for user in fort_server_obj.fortserveruser_set.all()]

                    resource = gen_resource(list(str(fort_server_obj.server.id)))
                    ans = ANSRunner(resource)
                    ans.run_module(host_list=fort_server_obj.server.assets.asset_management_ip,
                                   module_name='shell',
                                   module_args=r"cd /etc/sudoers.d/ && sed -i 's@{}@{}@' {}".format(old_format_commands,
                                                                                                    new_format_commands,
                                                                                                    ' '.join(
                                                                                                        sudo_users)))
                    res = ans.get_model_result()[0]
                    if 'success' in res:
                        FortBlackCommand.objects.filter(id=1).update(black_commands=new_black_commands)
                        return JsonResponse({'code': 200, 'msg': '更新成功！'})
                    else:
                        return JsonResponse({'code': 500, 'msg': '{}ansible更新失败！：{}'.format(
                            fort_server_obj.server.assets.asset_management_ip, res)})
            else:
                FortBlackCommand.objects.filter(id=1).update(black_commands=new_black_commands)
                return JsonResponse({'code': 200, 'msg': '更新成功！'})
        except Exception as e:
            return JsonResponse({'code': 500, 'msg': '更新失败！：{}'.format(e)})

    hosts = ServerAssets.objects.select_related('assets')
    server_status = FortServer.server_status_
    fort_user_status = FortServerUser.fort_user_status_
    auth_types = FortServerUser.auth_types
    users = UserProfile.objects.all()
    groups = Group.objects.all()
    return render(request, 'fort/fort_server.html', locals())


def format_commands(commands):
    command_list = []
    for command in commands.split(','):
        command_list.append('!' + command.strip())
    return ','.join(command_list)


@permission_required('Ops.add_fortserveruser', raise_exception=True)
def ssh_list(request):
    user = UserProfile.objects.get(username=request.user)
    groups = user.groups.all()
    fort_users = set(FortServerUser.objects.filter(Q(fort_belong_user=user) | Q(fort_belong_group__in=groups)))
    fort_servers = {fort_user.fort_server for fort_user in fort_users}

    return render(request, 'fort/ssh_list.html', locals())


@permission_required('Ops.ssh_fortserver', raise_exception=True)
def terminal(request, server_id, fort_user_id):
    server_ip = ServerAssets.objects.select_related('assets').get(id=server_id).assets.asset_management_ip
    fort_username = FortServerUser.objects.get(id=fort_user_id).fort_username
    return render(request, 'fort/terminal.html', locals())


@permission_required('Ops.add_fortrecord', raise_exception=True)
def login_fort_record(request):
    if request.method == 'GET':
        results = FortRecord.objects.select_related('login_user').all()
        return render(request, 'fort/login_fort_log.html', locals())
    elif request.method == 'POST':
        start_time = request.POST.get('startTime')
        end_time = request.POST.get('endTime')
        new_end_time = datetime.datetime.strptime(end_time, '%Y-%m-%d') + datetime.timedelta(1)
        end_time = new_end_time.strftime('%Y-%m-%d')
        try:
            records = []
            search_records = FortRecord.objects.select_related('login_user').filter(start_time__gt=start_time,
                                                                                    start_time__lt=end_time)
            for search_record in search_records:
                record = {
                    'id': search_record.id,
                    'login_user': search_record.login_user.username,
                    'fort': search_record.fort,
                    'remote_ip': search_record.remote_ip,
                    'start_time': search_record.start_time,
                    'login_status_time': search_record.login_status_time
                }
                records.append(record)
            return JsonResponse({'code': 200, 'records': records})
        except Exception as e:
            return JsonResponse({'code': 500, 'error': '查询失败：{}'.format(e)})


@permission_required('Ops.change_fortrecord', raise_exception=True)
def record_play(request, pk):
    record = FortRecord.objects.select_related('login_user').get(id=pk)
    return render(request, 'fort/record_play.html', locals())
