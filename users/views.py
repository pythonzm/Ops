from django.contrib.auth.hashers import make_password
from django.http import JsonResponse
from django.shortcuts import render
from users.models import UserProfile, UserPlan, UserRole
from django.contrib.auth.models import Group, Permission
from utils.decorators import admin_auth


def user_center(request):
    user = UserProfile.objects.get(username=request.user)

    if request.method == 'GET':
        my_plans = user.self_user.all() | user.attention_user.all()
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


def create_plan(request):
    if request.method == 'POST':
        try:
            user_plan = UserPlan.objects.create(
                user=UserProfile.objects.get(id=request.POST.get('user')),
                title=request.POST.get('title'),
                content=request.POST.get('content'),
                start_time=request.POST.get('start_time'),
                end_time=request.POST.get('end_time'),
            )
            attention = request.POST.getlist('attention')
            if attention:
                user_plan.attention.set(attention)
            return JsonResponse({'code': 200, 'result': True, 'msg': '数据保存成功！'})
        except Exception as e:
            return JsonResponse({'code': 500, 'result': False, 'msg': '数据保存失败！{}'.format(e)})
    users = UserProfile.objects.exclude(id__in=[request.user.id])
    return render(request, 'users/create_plan.html', locals())


def plan_info(request, pk):
    user_plan = UserPlan.objects.prefetch_related('attention').get(id=pk)
    if request.method == 'GET':
        users = UserProfile.objects.exclude(id__in=[request.user.id])
        return render(request, 'users/plan_info.html', locals())
    elif request.method == 'POST':
        try:
            user_plan.status = 1 if request.POST.get('status') else 0
            user_plan.title = request.POST.get('title')
            user_plan.content = request.POST.get('content')
            user_plan.start_time = request.POST.get('start_time')
            user_plan.end_time = request.POST.get('end_time')
            attention = request.POST.getlist('attention')
            if attention:
                user_plan.attention.set(attention)
            else:
                user_plan.attention.clear()
            user_plan.save()
            return JsonResponse({'code': 200, 'result': True, 'msg': '数据保存成功！'})
        except Exception as e:
            return JsonResponse({'code': 500, 'result': False, 'msg': '数据保存失败！{}'.format(e)})
    elif request.method == 'DELETE':
        try:
            user_plan.delete()
            return JsonResponse({'code': 200, 'result': True, 'msg': '数据删除成功！'})
        except Exception as e:
            return JsonResponse({'code': 500, 'result': False, 'msg': '数据删除失败！{}'.format(e)})


@admin_auth
def user_list(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        init_pass = username.capitalize() + '@123'
        try:
            user_obj = UserProfile.objects.create(
                username=username,
                password=make_password(init_pass),
                is_superuser=request.POST.get('is_superuser'),
                is_active=request.POST.get('is_active'),
                mobile=request.POST.get('mobile')
            )

            groups = request.POST.getlist('groups')
            if groups:
                user_obj.groups.set(groups)

            u_role = request.POST.getlist('u_role')
            if u_role:
                user_obj.userrole_set.set(u_role)
                perms = (UserRole.objects.get(id=pk).user_role_permissions.all() for pk in u_role)
                user_obj.user_permissions.set({i.id for p in perms for i in p})

            user_obj.save()

            return JsonResponse({"code": 201, "data": None, "msg": "用户添加成功！初始密码是{}".format(init_pass)})
        except Exception as e:
            return JsonResponse({"code": 500, "data": None, "msg": "用户添加失败，原因：{}".format(e)})
    groups = Group.objects.all().select_related()
    u_roles = UserRole.objects.all()
    return render(request, 'users/user_list.html', locals())


@admin_auth
def get_user(request):
    users = []
    try:
        for u in UserProfile.objects.all():
            users.append(get_user_data(u))
        return JsonResponse({"code": 200, "data": users, "msg": "用户获取成功！"})
    except Exception as e:
        return JsonResponse({"code": 500, "data": None, "msg": "用户获取失败，原因：{}".format(e)})


@admin_auth
def edit_user(request, pk):
    user = UserProfile.objects.get(id=pk)
    if request.method == 'POST':
        try:
            username = request.POST.get('username')
            is_superuser = request.POST.get('is_superuser')
            is_active = request.POST.get('is_active')
            mobile = request.POST.get('mobile')
            groups = request.POST.getlist('groups')
            u_role = request.POST.getlist('u_role')

            user.username = username
            user.is_superuser = is_superuser
            user.is_active = is_active
            user.mobile = mobile

            if groups:
                user.groups.set(groups)
            else:
                user.groups.clear()

            if u_role:
                user.userrole_set.set(u_role)
                perms = (UserRole.objects.get(id=pk).user_role_permissions.all() for pk in u_role)
                user.user_permissions.set({i.id for p in perms for i in p})
            else:
                user.userrole_set.clear()
                user.user_permissions.clear()

            user.save()
            return JsonResponse({"code": 200, "data": None, "msg": "用户更新成功！"})
        except Exception as e:
            return JsonResponse({"code": 500, "data": None, "msg": "用户更新失败，原因：{}".format(e)})
    data = get_user_data(user, info=False)
    return JsonResponse({"code": 200, "data": data, "msg": "用户获取成功！"})


@admin_auth
def delete_user(request, pk):
    if request.method == 'DELETE':
        try:
            UserProfile.objects.get(id=pk).delete()
            return JsonResponse({"code": 200, "data": None, "msg": "用户删除成功！"})
        except Exception as e:
            return JsonResponse({"code": 500, "data": None, "msg": "用户删除失败，原因：{}".format(e)})


def get_user_data(user, info=True):
    data = {'id': user.id, 'username': user.username, 'is_superuser': user.is_superuser, 'is_active': user.is_active,
            'mobile': user.mobile, 'groups': [g.name if info else g.id for g in user.groups.all()],
            'u_role': [r.user_role_name if info else r.id for r in user.userrole_set.all()]}
    return data


@admin_auth
def reset_password(request, pk):
    if request.method == 'POST':
        try:
            user = UserProfile.objects.get(id=pk)
            reset_pass = user.username.capitalize() + '@123'
            user.password = make_password(reset_pass)
            user.save()
            return JsonResponse({"code": 200, "data": None, "msg": "密码重置成功！密码为{}".format(reset_pass)})
        except Exception as e:
            return JsonResponse({"code": 500, "data": None, "msg": "密码重置失败，原因：{}".format(e)})


@admin_auth
def group_list(request):
    if request.method == 'POST':
        group_name = request.POST.get('group_name')
        users = request.POST.getlist('users')
        group_role = request.POST.getlist('group_role')
        try:
            group_obj = Group.objects.create(name=group_name)
            if users:
                group_obj.user_set.set(users)

            if group_role:
                group_obj.userrole_set.set(group_role)
                perms = (UserRole.objects.get(id=pk).user_role_permissions.all() for pk in group_role)
                group_obj.permissions.set({i.id for p in perms for i in p})
            group_obj.save()
            return JsonResponse({"code": 201, "data": None, "msg": "用户组添加成功！"})
        except Exception as e:
            return JsonResponse({"code": 500, "data": None, "msg": "用户组添加失败，原因：{}".format(e)})
    users = UserProfile.objects.all().select_related()
    group_roles = UserRole.objects.all()
    return render(request, 'users/group_list.html', locals())


@admin_auth
def get_group(request):
    groups = []
    try:
        for g in Group.objects.all():
            groups.append(get_group_data(g))
        return JsonResponse({"code": 200, "data": groups, "msg": "用户组获取成功！"})
    except Exception as e:
        return JsonResponse({"code": 500, "data": None, "msg": "用户组获取失败，原因：{}".format(e)})


@admin_auth
def edit_group(request, pk):
    group = Group.objects.get(id=pk)
    if request.method == 'POST':
        try:
            group_name = request.POST.get('group_name')
            users = request.POST.getlist('users')
            group_role = request.POST.getlist('group_role')
            group.name = group_name

            if users:
                group.user_set.set(users)
            else:
                group.user_set.clear()

            if group_role:
                group.userrole_set.set(group_role)
                perms = (UserRole.objects.get(id=pk).user_role_permissions.all() for pk in group_role)
                group.permissions.set({i.id for p in perms for i in p})
            else:
                group.userrole_set.clear()
                group.permissions.clear()
            group.save()
            return JsonResponse({"code": 200, "data": None, "msg": "用户组更新成功！"})
        except Exception as e:
            return JsonResponse({"code": 500, "data": None, "msg": "用户组更新失败，原因：{}".format(e)})
    data = get_group_data(group, info=False)
    return JsonResponse({"code": 200, "data": data, "msg": "用户组获取成功！"})


@admin_auth
def delete_group(request, pk):
    if request.method == 'DELETE':
        try:
            Group.objects.get(id=pk).delete()
            return JsonResponse({"code": 200, "data": None, "msg": "用户组删除成功！"})
        except Exception as e:
            return JsonResponse({"code": 500, "data": None, "msg": "用户组删除失败，原因：{}".format(e)})


def get_group_data(group, info=True):
    data = {'id': group.id, 'group_name': group.name,
            'users': [u.username if info else u.id for u in group.user_set.all()],
            'group_role': [r.user_role_name if info else r.id for r in group.userrole_set.all()]}
    return data


@admin_auth
def user_role_list(request):
    if request.method == 'POST':
        user_role_name = request.POST.get('user_role_name')
        user_role_permissions = request.POST.getlist('user_role_permissions')
        try:
            user_role_obj = UserRole.objects.create(user_role_name=user_role_name)
            user_role_obj.user_role_permissions.set(user_role_permissions)
            user_role_obj.save()
            return JsonResponse({"code": 201, "data": None, "msg": "角色添加成功！"})
        except Exception as e:
            return JsonResponse({"code": 500, "data": None, "msg": "角色添加失败，原因：{}".format(e)})
    pass_app_labels = ['admin', 'auth', 'celery_results', 'contenttypes', 'django_celery_beat', 'django_celery_results',
                       'sessions', 'sessions', 'users']
    permissions = (p for p in Permission.objects.all() if p.content_type.app_label not in pass_app_labels)
    return render(request, 'users/user_role_list.html', locals())


@admin_auth
def get_user_role(request):
    roles = []
    try:
        for r in UserRole.objects.prefetch_related('user_role_permissions').all():
            roles.append({'id': r.id, 'role_name': r.user_role_name,
                          'role_detail': [i.__str__() for i in r.user_role_permissions.all()]})
        return JsonResponse({"code": 200, "data": roles, "msg": "角色获取成功！"})
    except Exception as e:
        return JsonResponse({"code": 500, "data": None, "msg": "角色获取失败，原因：{}".format(e)})


@admin_auth
def edit_user_role(request, pk):
    role = UserRole.objects.prefetch_related('user_role_permissions').get(id=pk)
    if request.method == 'POST':
        try:
            user_role_name = request.POST.get('user_role_name')
            user_role_permissions = request.POST.getlist('user_role_permissions')
            role.user_role_name = user_role_name
            role.user_role_permissions.set(user_role_permissions)
            role.save()
            return JsonResponse({"code": 200, "data": None, "msg": "角色更新成功！"})
        except Exception as e:
            return JsonResponse({"code": 500, "data": None, "msg": "角色更新失败，原因：{}".format(e)})
    data = {'user_role_name': role.user_role_name,
            'user_role_permissions': [str(p.id) for p in role.user_role_permissions.all()]}
    return JsonResponse({"code": 200, "data": data, "msg": "角色获取成功！"})


@admin_auth
def delete_user_role(request, pk):
    if request.method == 'DELETE':
        try:
            UserRole.objects.get(id=pk).delete()
            return JsonResponse({"code": 200, "data": None, "msg": "角色删除成功！"})
        except Exception as e:
            return JsonResponse({"code": 500, "data": None, "msg": "角色删除失败，原因：{}".format(e)})
