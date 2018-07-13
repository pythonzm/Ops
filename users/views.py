from datetime import datetime
from django.contrib.auth.hashers import make_password
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render

from users.models import UserProfile, UserLog, UserPlan
from django.contrib.auth.models import Group, Permission
from django.core import serializers


def user_center(request):
    user = UserProfile.objects.get(username=request.user)

    if request.method == 'GET':
        events = UserPlan.objects.all()
        return render(request, 'users/user_center.html', locals())

    elif request.method == 'POST':
        if request.POST.get('password'):
            try:
                user.set_password(request.POST.get('password'))
                user.save()
                return JsonResponse({"code": 200, "data": None, "msg": "密码更新完毕，请重新使用新密码登录！"})
            except Exception as e:
                return JsonResponse({"code": 500, "data": None, "msg": "密码修改失败：%s" % str(e)})
        elif request.POST.get('mobile'):
            try:
                user.mobile = request.POST.get('mobile')
                user.save()
                return JsonResponse({"code": 200, "data": request.POST.get('mobile'), "msg": "手机号码更新完毕！"})
            except Exception as e:
                return JsonResponse({"code": 500, "data": None, "msg": "手机号码修改失败：%s" % str(e)})
        elif request.FILES.get('avatar'):
            try:
                avatar = request.FILES.get('avatar')
                user.image = avatar
                user.save()
                return JsonResponse({"code": 200, "data": None, "msg": "头像更新完毕！"})
            except Exception as e:
                return JsonResponse({"code": 500, "data": None, "msg": "头像更新失败：%s" % str(e)})
        elif request.FILES.get('title'):
            start_time = '{} {}'.format(request.POST.get('sdate'), request.POST.get('stime'))
            start_time = datetime.strptime(start_time, '%Y-%m-%d %H:%M:%S')
            end_time = '{} {}'.format(request.POST.get('edate'), request.POST.get('etime'))
            end_time = datetime.strptime(end_time, '%Y-%m-%d %H:%M:%S')
            UserPlan.objects.create(
                title=request.POST.get('title'),
                start_time=start_time,
                end_time=end_time,
                all_day=request.POST.get('allDay'),
            )
            data = {
                'title': request.POST.get('title'),
                'start': start_time,
                'end': end_time,
                'allDay': request.POST.get('allDay'),
            }
            return JsonResponse({'code': 200, 'data': data})


def get_user_list(request):
    user_list = UserProfile.objects.all().select_related()
    groups = Group.objects.all().select_related()
    permissions = Permission.objects.all().select_related()
    return render(request, 'users/user_list.html', locals())


def get_user_detail(request, pk):
    user = UserProfile.objects.get(id=pk)

    if request.method == 'POST':
        try:
            UserProfile.objects.filter(id=pk).update(
                is_superuser=request.POST.get('is_superuser'),
                username=request.POST.get('username'),
                is_active=request.POST.get('is_active'),
                mobile=request.POST.get('mobile')
            )

            # 修改用户组
            groups = request.POST.getlist('groups')
            if groups:
                user_group_set = set()
                for group in user.groups.values():
                    user_group_set.add(group.get('id'))

                group_set = {int(i) for i in groups}
                add_group_set = group_set.difference(user_group_set)
                del_group_set = user_group_set.difference(group_set)

                # 添加新增的用户组
                for group_id in add_group_set:
                    group_obj = Group.objects.get(id=group_id)
                    user.groups.add(group_obj)
                # 删除去掉的用户组
                for group_id in del_group_set:
                    group_obj = Group.objects.get(id=group_id)
                    user.groups.remove(group_obj)
            else:
                user.groups.clear()

            # 修改用户权限
            user_permissions = request.POST.getlist('user_permissions')
            if user_permissions:
                user_permission_set = set()
                for permission in user.user_permissions.values():
                    user_permission_set.add(permission.get('id'))

                permission_set = {int(i) for i in user_permissions}
                add_permission_set = permission_set.difference(user_permission_set)
                del_permission_set = user_permission_set.difference(permission_set)

                # 添加新增的用户权限
                for permission_id in add_permission_set:
                    permission_obj = Permission.objects.get(id=permission_id)
                    user.user_permissions.add(permission_obj)
                # 删除去掉的用户权限
                for permission_id in del_permission_set:
                    permission_obj = Permission.objects.get(id=permission_id)
                    user.user_permissions.remove(permission_obj)
            else:
                user.user_permissions.clear()

            return JsonResponse({"code": 200, "data": None, "msg": "更新成功！"})
        except Exception as e:
            return JsonResponse({"code": 500, "data": None, "msg": '更新用户信息失败，原因：{}'.format(e)})

    elif request.method == 'GET':
        groups = Group.objects.all().select_related()
        permissions = Permission.objects.all().select_related()
        return render(request, 'users/user_detail.html', locals())


def create_user(request):
    if request.method == 'POST':
        try:
            UserProfile.objects.create(
                username=request.POST.get('username'),
                password=make_password('123456'),
                is_superuser=request.POST.get('is_superuser'),
                is_active=request.POST.get('is_active'),
                mobile=request.POST.get('mobile')
            )

            user = UserProfile.objects.get(username=request.POST.get('username'))
            groups = request.POST.getlist('groups')
            if groups:
                for i in groups:
                    group = Group.objects.get(id=i)
                    user.groups.add(group)

            user_permissions = request.POST.getlist('user_permissions')
            if user_permissions:
                for i in user_permissions:
                    permission = Permission.objects.get(id=i)
                    user.user_permissions.add(permission)

            return JsonResponse({"code": 200, "data": None, "msg": "用户添加成功！初始密码是123456"})
        except Exception as e:
            return JsonResponse({"code": 500, "data": None, "msg": "用户添加失败，原因：{}".format(e)})


def reset_password(request, pk):
    if request.method == 'POST':
        try:
            UserProfile.objects.filter(id=pk).update(
                password=make_password('123456')
            )

            return JsonResponse({"code": 200, "data": None, "msg": "密码重置成功！密码为123456"})
        except Exception as e:
            return JsonResponse({"code": 500, "data": None, "msg": "密码重置失败，原因：{}".format(e)})


def get_group_list(request):
    groups = Group.objects.all().select_related()
    users = UserProfile.objects.all()
    permissions = Permission.objects.all().select_related()
    return render(request, 'users/group_list.html', locals())


def get_group_detail(request, pk):
    group = Group.objects.get(id=pk)

    if request.method == 'POST':
        try:
            Group.objects.filter(id=pk).update(
                name=request.POST.get('groupname'),
            )

            # 修改用户
            users = request.POST.getlist('users')
            if users:
                group_users_set = set()
                for user in group.user_set.values():
                    group_users_set.add(user.get('id'))

                users_set = {int(i) for i in users}
                add_users_set = users_set.difference(group_users_set)
                del_users_set = group_users_set.difference(users_set)

                # 添加新增的用户
                for user_id in add_users_set:
                    user_obj = UserProfile.objects.get(id=user_id)
                    group.user_set.add(user_obj)
                # 删除去掉的用户
                for user_id in del_users_set:
                    user_obj = UserProfile.objects.get(id=user_id)
                    group.user_set.remove(user_obj)
            else:
                group.user_set.clear()

            # 修改用户组权限
            group_permissions = request.POST.getlist('group_permissions')
            if group_permissions:
                group_permission_set = set()
                for permission in group.permissions.values():
                    group_permission_set.add(permission.get('id'))

                permission_set = {int(i) for i in group_permissions}
                add_permission_set = permission_set.difference(group_permission_set)
                del_permission_set = group_permission_set.difference(permission_set)

                # 添加新增的用户权限
                for permission_id in add_permission_set:
                    permission_obj = Permission.objects.get(id=permission_id)
                    group.permissions.add(permission_obj)
                # 删除去掉的用户权限
                for permission_id in del_permission_set:
                    permission_obj = Permission.objects.get(id=permission_id)
                    group.permissions.remove(permission_obj)
            else:
                group.permissions.clear()

            return JsonResponse({"code": 200, "data": None, "msg": "更新成功！"})
        except Exception as e:
            return JsonResponse({"code": 500, "data": None, "msg": '更新用户组信息失败，原因：{}'.format(e)})

    elif request.method == 'GET':
        users = UserProfile.objects.all().select_related()
        permissions = Permission.objects.all().select_related()
        return render(request, 'users/group_detail.html', locals())


def create_group(request):
    if request.method == 'POST':
        try:
            Group.objects.create(
                name=request.POST.get('groupname'),
            )

            group = Group.objects.get(name=request.POST.get('groupname'))
            users = request.POST.getlist('users')
            if users:
                for i in users:
                    user = UserProfile.objects.get(id=i)
                    group.user_set.add(user)

            group_permissions = request.POST.getlist('group_permissions')
            if group_permissions:
                for i in group_permissions:
                    permission = Permission.objects.get(id=i)
                    group.permissions.add(permission)

            return JsonResponse({"code": 200, "data": None, "msg": "用户组添加成功"})
        except Exception as e:
            return JsonResponse({"code": 500, "data": None, "msg": "用户组添加失败，原因：{}".format(e)})


def get_user_log(request):
    if request.method == 'GET':
        user_logs = UserLog.objects.all()
        return render(request, 'users/user_log.html', locals())
    elif request.method == 'POST':
        start_time = request.POST.get('startTime')
        end_time = request.POST.get('endTime')
        try:
            user_logs = UserLog.objects.filter(c_time__gte=start_time, c_time__lte=end_time)
            user_logs = serializers.serialize('json', user_logs)
            return HttpResponse(user_logs)
        except Exception as e:
            return JsonResponse({'error': '查询失败：{}'.format(e)})
