# -*- coding: utf-8 -*-
from django.contrib import auth
from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import redirect, render
from django.contrib.auth.decorators import login_required
from assets.models import *
from users.models import UserProfile
from utils.db.redis_ops import RedisOps
from Ops import settings

c = RedisOps(settings.REDIS_HOST, settings.REDIS_PORT, db=5)


@login_required()
def dashboard(request):
    assets_count = Assets.objects.all().count()
    project_count = Project.objects.all().count()
    users = UserProfile.objects.all()
    return render(request, 'dashboard.html', locals())


def pub_chat(channel, message):
    c.publish(channel, message)


def login(request):
    if request.session.get('username') and request.session.get('lock'):
        del request.session['lock']
        del request.session['username']
        return render(request, 'login.html')
    else:
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = auth.authenticate(username=username, password=password)
        if user and user.is_active:
            auth.login(request, user)
            request.session['username'] = username
            UserProfile.objects.filter(username=username).update(
                login_status=0
            )
            return HttpResponseRedirect('/users/user_center/', locals())
        else:
            if request.method == "POST":
                return render(request, 'login.html', {"login_error_info": "用户名不错存在，或者密码错误！"}, )
            else:
                return render(request, 'login.html')


def logout(request):
    c.unsubscribe(request.user)
    UserProfile.objects.filter(username=request.user).update(
        login_status=1
    )
    auth.logout(request)
    return HttpResponseRedirect('/login/')


def lock_screen(request):
    if request.method == 'GET':
        user = UserProfile.objects.get(username=request.user)
        request.session['lock'] = 'lock'
        return render(request, 'lockscreen.html', locals())
    elif request.method == 'POST':
        user = auth.authenticate(username=request.session['username'], password=request.POST.get('pwd'))
        if user:
            del request.session['lock']
            return redirect('/')
        return render(request, 'lockscreen.html', {"login_error_info": "密码错误！请确认输入的密码是否正确！"}, )
