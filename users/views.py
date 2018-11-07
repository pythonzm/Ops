import datetime
from django.contrib.auth.hashers import make_password
from django.http import JsonResponse
from django.shortcuts import render
from users.models import UserProfile, UserLog
from django.contrib.auth.models import Group, Permission
from django.contrib.auth.decorators import permission_required


def user_center(request):
    user = UserProfile.objects.get(username=request.user)

    if request.method == 'GET':
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


@permission_required('users.add_userprofile', raise_exception=True)
def get_user_list(request):
    user_list = UserProfile.objects.all().select_related()
    groups = Group.objects.all().select_related()
    permissions = Permission.objects.all().select_related()
    return render(request, 'users/user_list.html', locals())


@permission_required('users.add_userprofile', raise_exception=True)
def create_user(request):
    if request.method == 'POST':
        try:
            user_obj = UserProfile.objects.create(
                username=request.POST.get('username'),
                password=make_password('123456'),
                is_superuser=request.POST.get('is_superuser'),
                is_active=request.POST.get('is_active'),
                mobile=request.POST.get('mobile')
            )

            data = {
                'id': user_obj.id,
                'username': user_obj.username,
                'is_superuser': user_obj.is_superuser,
                'is_active': user_obj.is_active,
                'mobile': user_obj.mobile
            }

            groups = request.POST.getlist('groups')
            if groups:
                for i in groups:
                    group = Group.objects.get(id=i)
                    user_obj.groups.add(group)

            user_permissions = request.POST.getlist('user_permissions')
            if user_permissions:
                for i in user_permissions:
                    permission = Permission.objects.get(id=i)
                    user_obj.user_permissions.add(permission)

            return JsonResponse({"code": 200, "data": data, "msg": "用户添加成功！初始密码是123456"})
        except Exception as e:
            return JsonResponse({"code": 500, "data": None, "msg": "用户添加失败，原因：{}".format(e)})


@permission_required('users.change_userprofile', raise_exception=True)
def reset_password(request, pk):
    if request.method == 'POST':
        try:
            UserProfile.objects.filter(id=pk).update(
                password=make_password('123456')
            )

            return JsonResponse({"code": 200, "data": None, "msg": "密码重置成功！密码为123456"})
        except Exception as e:
            return JsonResponse({"code": 500, "data": None, "msg": "密码重置失败，原因：{}".format(e)})


@permission_required('auth.add_group', raise_exception=True)
def get_group_list(request):
    groups = Group.objects.all().select_related()
    users = UserProfile.objects.all().select_related()
    permissions = Permission.objects.all().select_related()
    return render(request, 'users/group_list.html', locals())


@permission_required('users.add_userlog', raise_exception=True)
def get_user_log(request):
    if request.method == 'GET':
        user_logs = UserLog.objects.all()
        return render(request, 'users/user_log.html', locals())
    elif request.method == 'POST':
        start_time = request.POST.get('startTime')
        end_time = request.POST.get('endTime')
        new_end_time = datetime.datetime.strptime(end_time, '%Y-%m-%d') + datetime.timedelta(1)
        end_time = new_end_time.strftime('%Y-%m-%d')
        try:
            records = []
            user_logs = UserLog.objects.filter(c_time__gt=start_time, c_time__lt=end_time)
            for user_log in user_logs:
                record = {
                    'id': user_log.id,
                    'user': user_log.user.username,
                    'remote_ip': user_log.remote_ip,
                    'content': user_log.content,
                    'c_time': user_log.c_time
                }
                records.append(record)
            return JsonResponse({'code': 200, 'records': records})
        except Exception as e:
            return JsonResponse({'code': 500, 'error': '查询失败：{}'.format(e)})
