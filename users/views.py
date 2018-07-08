from django.contrib.auth.hashers import make_password
from django.http import JsonResponse
from django.shortcuts import render
from users.models import UserProfile
from django.contrib.auth.models import Group, Permission
from conf.logger import user_logger


def user_center(request):
    if request.method == 'GET':
        user = UserProfile.objects.get(id=4)
        return render(request, 'users/user_center.html', locals())


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

            return JsonResponse({'msg': '更新成功'})
        except Exception as e:
            user_logger.error('更新用户信息失败，原因：{}'.format(e))

    elif request.method == 'GET':
        groups = Group.objects.all().select_related()
        permissions = Permission.objects.all().select_related()
        return render(request, 'users/user_detail.html', locals())


def create_user(request):
    if request.method == 'POST':
        try:
            UserProfile.objects.create(
                username=request.POST.get('username'),
                password=make_password(request.POST.get('password')),
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

            return JsonResponse({"code": 200, "data": None, "msg": "用户添加成功"})
        except Exception as e:
            return JsonResponse({"code": 500, "data": None, "msg": "用户注册失败，原因：{}".format(e)})


def get_group_list(request):
    groups = Group.objects.all().select_related()
    return render(request, 'users/group_list.html', locals())
