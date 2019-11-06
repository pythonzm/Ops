import datetime
import uuid
import os
from django.http import JsonResponse, HttpResponseForbidden
from django.shortcuts import render
from fort.models import *
from assets.models import ServerAssets
from django.contrib.auth.models import Group
from users.models import UserProfile
from task.utils.gen_resource import GenResource
from task.utils.ansible_api_v2 import ANSRunner
from django.contrib.auth.decorators import permission_required
from django.conf import settings
from utils.sftp import SFTP
from utils.decorators import admin_auth


@admin_auth
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

                    resource = GenResource().gen_host_list(list(str(fort_server_obj.server.id)))
                    ans = ANSRunner(resource)
                    ans.run_module(host_list=fort_server_obj.server.assets.asset_management_ip,
                                   module_name='shell',
                                   module_args=r"cd /etc/sudoers.d/ && sed -i 's@{}@{}@' {}".format(
                                       old_format_commands,
                                       new_format_commands,
                                       ' '.join(
                                           sudo_users)))
                    FortBlackCommand.objects.filter(id=1).update(black_commands=new_black_commands)
                    return JsonResponse({'code': 200, 'msg': '更新成功！'})
            else:
                FortBlackCommand.objects.filter(id=1).update(black_commands=new_black_commands)
                return JsonResponse({'code': 200, 'msg': '更新成功！'})
        except Exception as e:
            return JsonResponse({'code': 500, 'msg': '更新失败！：{}'.format(e)})

    hosts = ServerAssets.objects.select_related('assets')
    server_protocols = FortServer.server_protocols
    server_status = FortServer.server_status_
    fort_user_status = FortServerUser.fort_user_status_
    users = UserProfile.objects.all()
    groups = Group.objects.all()
    remote_ip = request.META['REMOTE_ADDR']
    return render(request, 'fort/fort_server.html', locals())


def format_commands(commands):
    command_list = []
    for command in commands.split(','):
        command_list.append('!' + command.strip())
    return ','.join(command_list)


@permission_required('fort.ssh_fortserver', raise_exception=True)
def ssh_list(request):
    fort_users = gen_fort_users(request.user)
    return render(request, 'fort/ssh_list.html', locals())


@permission_required('fort.ssh_fortserver', raise_exception=True)
def terminal(request, server_id, fort_user_id):
    server_obj = ServerAssets.objects.select_related('assets').get(id=server_id)
    fort_user_obj = FortServerUser.objects.get(id=fort_user_id)
    fort_username = fort_user_obj.fort_username
    server_ip = server_obj.assets.asset_management_ip

    if request.method == 'GET':
        download_file = request.GET.get('download_file')
        if download_file:

            download_file_path = os.path.join(settings.MEDIA_ROOT, 'fort_files', request.user.username, 'download',
                                              server_ip)
            sftp = SFTP(server_ip, server_obj.port, fort_username,
                        fort_user_obj.fort_password)

            response = sftp.download_file(download_file, download_file_path)
            return response
        else:
            fort_users = gen_fort_users(request.user)

            if fort_user_obj in fort_users:
                remote_ip = request.META.get('REMOTE_ADDR')
                if fort_user_obj.fort_server.server_protocol == 'ssh':
                    return render(request, 'fort/terminal.html', locals())
                else:
                    group_name = str(uuid.uuid4())
                    return render(request, 'fort/guacamole.html', locals())
            else:
                return HttpResponseForbidden('<h1>403！您无权连接此主机！</h1>')
    elif request.method == 'POST':
        try:
            upload_file = request.FILES.get('upload_file')
            upload_file_path = os.path.join(settings.MEDIA_ROOT, 'fort_files', request.user.username, 'upload',
                                            server_obj.assets.asset_management_ip)
            sftp = SFTP(server_ip, server_obj.port, fort_username,
                        fort_user_obj.fort_password)

            sftp.upload_file(upload_file, upload_file_path)

            return JsonResponse({'code': 200, 'msg': '上传成功！文件默认放在/home/{}路径下'.format(fort_username)})
        except Exception as e:
            return JsonResponse({'code': 500, 'msg': '上传失败！{}'.format(e)})


def gen_fort_users(user):
    """
    生成当前用户下的所有可用的用户列表
    :param user: 当前用户，request.user
    """
    groups = user.groups.all()

    fort_server_users = FortServerUser.objects.prefetch_related('fort_belong_group').all()

    fort_users = {i for i in FortServerUser.objects.prefetch_related('fort_belong_user').filter(fort_belong_user=user)}

    for fort_server_user in fort_server_users:
        if not set(fort_server_user.fort_belong_group.all()).isdisjoint(set(groups)):  # 判断fort_user的组与当前用户的组是否有交集
            fort_users.add(fort_server_user)

    fort_users = [user for user in fort_users if user.fort_server.server_status == 1 and user.fort_user_status == 1]

    users = fort_server_users if user.is_superuser else fort_users
    return users


@admin_auth
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
                    'record_mode': search_record.get_record_mode_display(),
                    'remote_ip': search_record.remote_ip,
                    'start_time': search_record.start_time,
                    'login_status_time': search_record.login_status_time,
                    'record_cmds': search_record.record_cmds
                }
                records.append(record)
            return JsonResponse({'code': 200, 'records': records})
        except Exception as e:
            return JsonResponse({'code': 500, 'error': '查询失败：{}'.format(e)})


@admin_auth
def record_play(request, pk):
    record = FortRecord.objects.select_related('login_user').get(id=pk)
    if record.record_mode == 'ssh':
        return render(request, 'fort/ssh_record_play.html', locals())
    else:
        return render(request, 'fort/guacamole_record_play.html', locals())
