# -*- coding: utf-8 -*-
from django.contrib import auth
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from assets.models import *
from users.models import UserProfile


@login_required()
def dashboard(request):
    assets_count = Assets.objects.all().count()
    project_count = Project.objects.all().count()
    user_count = UserProfile.objects.all().count()
    return render(request, 'dashboard.html', locals())


def login(request):
    if request.session.get('username') is not None:
        return HttpResponseRedirect('/', {"user": request.user})
    else:
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = auth.authenticate(username=username, password=password)
        if user and user.is_active:
            auth.login(request, user)
            request.session['username'] = username
            return HttpResponseRedirect('/', locals())
        else:
            if request.method == "POST":
                return render(request, 'login.html', {"login_error_info": "用户名不错存在，或者密码错误！"}, )
            else:
                return render(request, 'login.html')


def logout(request):
    auth.logout(request)
    return HttpResponseRedirect('/login/')
