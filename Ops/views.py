# -*- coding: utf-8 -*-
import random
from django.contrib import auth
from django.http import HttpResponseRedirect, HttpResponseForbidden, HttpResponse
from django.shortcuts import redirect, render
from assets.models import *
from users.models import UserProfile
from projs.models import Project
from fort.models import FortServer
from utils.gen_random_code import generate
from utils.crypt_pwd import CryptPwd
from io import BytesIO
from plan.tasks import get_login_info


def dashboard(request):
    if request.user.is_superuser:
        assets_count = Assets.objects.count()
        project_count = Project.objects.count()
        user_count = UserProfile.objects.count()
        fort_server_count = FortServer.objects.count()
        zabbix_alerts = ZabbixAlert.objects.all()
        websites = WebSite.objects.all()
        return render(request, 'dashboard.html', locals())
    else:
        return HttpResponseForbidden('<h1>403 Forbidden</h1>', content_type='text/html')


def gen_code_img(request):
    f = BytesIO()
    img, code = generate(fg_color=(random.randint(10, 300), random.randint(50, 150), random.randint(50, 150)))
    request.session['check_code'] = code
    img.save(f, 'PNG')
    return HttpResponse(f.getvalue())


def login(request):
    next_url = request.GET.get('next', None)
    crypt = CryptPwd()
    if request.method == 'GET':
        if request.session.get('username') and request.session.get('lock'):
            del request.session['lock']
            del request.session['username']
        return render(request, 'login.html')
    elif request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        de_password = crypt.de_js_encrypt(password)
        login_ip = request.META.get('REMOTE_ADDR')
        # code = request.POST.get('code')
        remember_me = request.POST.get('remember_me')
        # if code.lower() != request.session.get('check_code', 'error').lower():
        #     return render(request, 'login.html', {"login_error_info": "验证码错误,请重新输入！"})
        user = auth.authenticate(username=username, password=de_password)
        if user and user.is_active:
            auth.login(request, user)
            request.session['username'] = username
            if remember_me:
                request.session.set_expiry(60 * 60 * 24 * 7)
            else:
                request.session.set_expiry(0)
            UserProfile.objects.filter(username=username).update(
                login_status=0
            )
            get_login_info.delay(login_user=username, login_ip=login_ip, login_status='登录成功')

            if next_url:
                if next_url == '/' and not user.is_superuser:
                    return HttpResponseRedirect('/users/user_center/', locals())
                return HttpResponseRedirect(next_url, locals())
            else:
                return HttpResponseRedirect('/users/user_center/', locals())
        elif user is None:
            get_login_info.delay(login_user=username, login_ip=login_ip, login_status='登录失败')
            return render(request, 'login.html', {"login_error_info": "输入的用户名或密码错误！"})
        elif not user.is_active:
            return render(request, 'login.html', {"login_error_info": "账户被禁用！"})
        else:
            return render(request, 'login.html', {"login_error_info": "未知异常，请联系管理员！"})


def logout(request):
    UserProfile.objects.filter(username=request.user).update(
        login_status=1
    )
    auth.logout(request)
    return HttpResponseRedirect('/login/')


def lock_screen(request):
    if request.method == 'GET':
        user = UserProfile.objects.get(username=request.user)
        UserProfile.objects.filter(username=request.user).update(
            login_status=3
        )
        request.session['lock'] = 'lock'
        if 'lock_screen' not in request.META.get('HTTP_REFERER'):
            request.session['referer_url'] = request.META.get('HTTP_REFERER')
        return render(request, 'lockscreen.html', locals())
    elif request.method == 'POST':
        de_password = CryptPwd().de_js_encrypt(request.POST.get('pwd'))
        user = auth.authenticate(username=request.session['username'], password=de_password)
        if user:
            del request.session['lock']
            referer_url = request.session.get('referer_url')
            return redirect(referer_url)
        return render(request, 'lockscreen.html', {"login_error_info": "密码错误！请确认输入的密码是否正确！"}, )
