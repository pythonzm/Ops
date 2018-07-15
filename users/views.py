import random
import json
from datetime import datetime
from django.db.models import Q
from django.contrib.auth.hashers import make_password
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render

from users.models import UserProfile, UserLog, UserPlan
from django.contrib.auth.models import Group, Permission
from django.core import serializers


def user_center(request):
    user = UserProfile.objects.get(username=request.user)

    if request.method == 'GET':
        events = UserPlan.objects.filter(user=user)
        users = UserProfile.objects.all()
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
        elif request.POST.get('title'):
            start_time = '{} {}'.format(request.POST.get('sdate'), request.POST.get('stime'))
            start_time = datetime.strptime(start_time, '%Y-%m-%d %H:%M:%S')
            end_time = '{} {}'.format(request.POST.get('edate'), request.POST.get('etime'))
            end_time = datetime.strptime(end_time, '%Y-%m-%d %H:%M:%S')
            add_users = request.POST.get('add_users')

            chars = '0123456789abcdef'
            color = '#{}'.format(''.join(random.sample(chars, 6)))

            if add_users:
                add_users = json.loads(add_users)
                for user_id in add_users:
                    UserPlan.objects.update_or_create(
                        user=UserProfile.objects.get(id=user_id),
                        title=request.POST.get('title'),
                        start_time=start_time,
                        end_time=end_time,
                        all_day=request.POST.get('allDay'),
                        color=color
                    )
            UserPlan.objects.update_or_create(
                user=user,
                title=request.POST.get('title'),
                start_time=start_time,
                end_time=end_time,
                all_day=request.POST.get('allDay'),
                color=color
            )

            data = {
                'title': request.POST.get('title'),
                'start': start_time,
                'end': end_time,
                'allDay': request.POST.get('allDay'),
                'backgroundColor': color,
                'borderColor': color,
            }
            return JsonResponse({'code': 200, 'data': data})


def del_user_plan(request):
    try:
        if request.method == 'POST':
            title = request.POST.get('title')
            UserPlan.objects.get(Q(user=UserProfile.objects.get(username=request.user)) & Q(title=title)).delete()
            return JsonResponse({"code": 200, "data": None, "msg": "删除成功！"})
    except Exception as e:
        return JsonResponse({"code": 200, "data": None, "msg": "删除失败！，原因：{}".format(e)})


def get_user_list(request):
    user_list = UserProfile.objects.all().select_related()
    groups = Group.objects.all().select_related()
    permissions = Permission.objects.all().select_related()
    return render(request, 'users/user_list.html', locals())


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
    users = UserProfile.objects.all().select_related()
    permissions = Permission.objects.all().select_related()
    return render(request, 'users/group_list.html', locals())


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
