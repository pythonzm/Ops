from django.db.models import Q
from django.shortcuts import render
from fort.models import FortServer, FortServerUser
from assets.models import ServerAssets
from django.contrib.auth.models import Group
from users.models import UserProfile


def fort_server(request):
    fort_servers = FortServer.objects.select_related('server')
    fort_users = FortServerUser.objects.select_related('fort_server')
    hosts = ServerAssets.objects.select_related('assets')
    server_status = FortServer.server_status_
    fort_user_status = FortServerUser.fort_user_status_
    auth_types = FortServerUser.auth_types
    users = UserProfile.objects.all()
    groups = Group.objects.all()
    return render(request, 'fort/fort_server.html', locals())


def ssh_list(request):
    user = UserProfile.objects.get(username=request.user)
    groups = user.groups.all()
    fort_users = set(FortServerUser.objects.filter(Q(fort_belong_user=user) | Q(fort_belong_group__in=groups)))
    fort_servers = {fort_user.fort_server for fort_user in fort_users}

    return render(request, 'fort/ssh_list.html', locals())


def terminal(request, server_id, fort_user_id):
    server_ip = ServerAssets.objects.select_related('assets').get(id=server_id).assets.asset_management_ip
    fort_username = FortServerUser.objects.get(id=fort_user_id).fort_username
    return render(request, 'fort/terminal.html', locals())
