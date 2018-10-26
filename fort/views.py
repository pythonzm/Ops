import datetime
import os
from django.db.models import Q
from django.http import JsonResponse, HttpResponseForbidden, FileResponse
from django.shortcuts import render
from fort.models import *
from assets.models import ServerAssets
from django.contrib.auth.models import Group
from users.models import UserProfile
from task.views import gen_resource
from task.utils.ansible_api_v2 import ANSRunner
from django.contrib.auth.decorators import permission_required
from Ops import settings
from utils.sftp import SFTP


def fort_server(request):
    if request.user.is_superuser:
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
                                       module_args=r"cd /etc/sudoers.d/ && sed -i 's@{}@{}@' {}".format(
                                           old_format_commands,
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
        users = UserProfile.objects.all()
        groups = Group.objects.all()
        return render(request, 'fort/fort_server.html', locals())
    else:
        return HttpResponseForbidden('<h1>403</h1>')


def format_commands(commands):
    command_list = []
    for command in commands.split(','):
        command_list.append('!' + command.strip())
    return ','.join(command_list)


@permission_required('fort.ssh_fortserver', raise_exception=True)
def ssh_list(request):
    user = UserProfile.objects.get(username=request.user)
    groups = user.groups.all()
    fort_users = set(FortServerUser.objects.filter(Q(fort_belong_user=user) | Q(fort_belong_group__in=groups)))
    fort_servers = {fort_user.fort_server for fort_user in fort_users}

    return render(request, 'fort/ssh_list.html', locals())


@permission_required('fort.ssh_fortserver', raise_exception=True)
def terminal(request, server_id, fort_user_id):
    server_obj = ServerAssets.objects.select_related('assets').get(id=server_id)
    fort_user_obj = FortServerUser.objects.get(id=fort_user_id)
    fort_username = fort_user_obj.fort_username
    sftp = SFTP(server_obj.assets.asset_management_ip, server_obj.port, fort_username,
                fort_user_obj.fort_password)
    if request.method == 'GET':
        server_ip = server_obj.assets.asset_management_ip
        download_file = request.GET.get('download_file')
        if download_file:
            download_file_path = os.path.join(settings.MEDIA_ROOT, 'fort_files', request.user.username, 'download',
                                              server_ip)
            local_file_name = download_file.split('/')[-1]

            if not os.path.exists(download_file_path):
                os.makedirs(download_file_path, exist_ok=True)

            local_file = '{}/{}'.format(download_file_path, local_file_name)
            download_file_size = sftp.sftp.stat(download_file).st_size

            sftp.get_file(download_file, local_file)

            local_file_size = None
            while local_file_size != download_file_size:
                local_file_size = os.path.getsize(local_file)

            response = FileResponse(open(local_file, 'rb'))
            response['Content-Type'] = 'application/octet-stream'
            response['Content-Disposition'] = 'attachment;filename="{filename}"'.format(filename=local_file_name)
            return response
        else:
            return render(request, 'fort/terminal.html', locals())
    elif request.method == 'POST':
        try:
            upload_file = request.FILES.get('upload_file')
            upload_file_path = os.path.join(settings.MEDIA_ROOT, 'fort_files', request.user.username, 'upload',
                                            server_obj.assets.asset_management_ip)
            if not os.path.exists(upload_file_path):
                os.makedirs(upload_file_path, exist_ok=True)

            local_file = '{}/{}'.format(upload_file_path, upload_file.name)

            if not os.path.exists(local_file):
                open(local_file, 'w').close()
            local_file_size = None

            while local_file_size != upload_file.size:
                with open(local_file, 'wb') as f:
                    for chunk in upload_file.chunks():
                        f.write(chunk)
                local_file_size = os.path.getsize(local_file)

            sftp.put_file(local_file, '/home/{}'.format(fort_username))

            return JsonResponse({'code': 200, 'msg': '上传成功！文件默认放在/home/{}路径下'.format(fort_username)})
        except Exception as e:
            return JsonResponse({'code': 500, 'msg': '上传失败！{}'.format(e)})


def login_fort_record(request):
    if request.user.is_superuser:
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
    else:
        return HttpResponseForbidden('<h1>403</h1>')


def record_play(request, pk):
    if request.user.is_superuser:
        record = FortRecord.objects.select_related('login_user').get(id=pk)
        return render(request, 'fort/record_play.html', locals())
    else:
        return HttpResponseForbidden('<h1>403</h1>')
