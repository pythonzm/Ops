import json
import datetime
import random
from django.contrib import auth
from django.http import HttpResponseRedirect, HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from assets.models import *
from users.models import UserProfile
from projs.models import Project
from fort.models import FortServer
from utils.gen_random_code import generate
from utils.decorators import admin_auth
from utils.crypt_pwd import CryptPwd
from utils.db.mongo_ops import MongoOps, JSONEncoder
from io import BytesIO
from django.conf import settings
from commons.tasks import get_login_info


@admin_auth
def dashboard(request):
    assets_count = Assets.objects.count()
    project_count = Project.objects.count()
    user_count = UserProfile.objects.count()
    fort_server_count = FortServer.objects.count()
    zabbix_alerts = ZabbixAlert.objects.all()
    websites = WebSite.objects.all()
    return render(request, 'dashboard.html', locals())


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
        return render(request, 'login.html', {'public_key': crypt.gen_pri_pub_key})
    elif request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        de_password = crypt.de_js_encrypt(password)

        login_ip = request.META.get('REMOTE_ADDR')
        code = request.POST.get('code')
        remember_me = request.POST.get('remember_me')
        if code.lower() != request.session.get('check_code', 'error').lower():
            return render(request, 'login.html', {"login_error_info": "验证码错误,请重新输入！", 'public_key': crypt.gen_pri_pub_key})
        user = auth.authenticate(username=username, password=de_password)
        if user and user.is_active:
            auth.login(request, user)
            request.session['username'] = username
            if remember_me:
                request.session.set_expiry(60 * 60 * 24 * 7)
            else:
                request.session.set_expiry(60 * 60 * 8)
            UserProfile.objects.filter(username=username).update(
                login_status=0
            )
            #get_login_info.delay(login_user=username, login_ip=login_ip, login_status='登录成功')

            if next_url:
                if next_url == '/' and not user.is_superuser:
                    return HttpResponseRedirect('/users/user_center/', locals())
                return HttpResponseRedirect(next_url, locals())
            else:
                return HttpResponseRedirect('/users/user_center/', locals())
        elif user is None:
            #get_login_info.delay(login_user=username, login_ip=login_ip, login_status='登录失败')
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
    crypt = CryptPwd()
    if request.method == 'GET':
        user = UserProfile.objects.get(username=request.user)
        UserProfile.objects.filter(username=request.user).update(
            login_status=3
        )
        request.session['lock'] = 'lock'
        if 'lock_screen' not in request.META.get('HTTP_REFERER'):
            request.session['referer_url'] = request.META.get('HTTP_REFERER')
        public_key = crypt.gen_pri_pub_key
        return render(request, 'lockscreen.html', locals())
    elif request.method == 'POST':
        de_password = crypt.de_js_encrypt(request.POST.get('pwd'))
        user = auth.authenticate(username=request.session['username'], password=de_password)
        if user:
            del request.session['lock']
            referer_url = request.session.get('referer_url')
            return redirect(referer_url)
        return render(request, 'lockscreen.html',
                      {"login_error_info": "密码错误！请确认输入的密码是否正确！", 'public_key': crypt.gen_pri_pub_key})


@admin_auth
def system_log(request):
    return render(request, 'system_log.html')


# datatables客户端分页(一次性获取所有数据)
# @admin_auth
# def get_system_log(request):
#     mongo = MongoOps(settings.MONGODB_HOST, settings.MONGODB_PORT, settings.RECORD_DB, settings.RECORD_COLL)
#     start_time = request.GET.get('startTime')
#     end_time = request.GET.get('endTime')
#     try:
#         if start_time and end_time:
#             start_time = datetime.datetime.strptime(start_time, '%Y-%m-%d')
#             end_time = datetime.datetime.strptime(end_time, '%Y-%m-%d') + datetime.timedelta(1)
#             return_data = mongo.find({"datetime": {"$gt": start_time, "$lt": end_time}})
#         else:
#             return_data = mongo.find()
#         return JsonResponse({'code': 200, 'data': return_data, 'msg': '获取成功'}, encoder=JSONEncoder)
#     except Exception as e:
#         return JsonResponse({'code': 500, 'data': None, 'msg': '获取失败，{}'.format(e)})

# datatables服务端分页
@admin_auth
def get_system_log(request):
    mongo = MongoOps(settings.MONGODB_HOST, settings.MONGODB_PORT, settings.RECORD_DB, settings.RECORD_COLL,
                     settings.MONGODB_USER, settings.MONGODB_PASS)
    draw = int(request.GET.get('draw'))  # 记录操作次數
    start = int(request.GET.get('start'))  # 起始位置
    length = int(request.GET.get('length'))  # 每页长度
    start_time = request.GET.get('startTime')
    end_time = request.GET.get('endTime')
    log_user = request.GET.get('logUser')
    log_path = request.GET.get('logPath')

    # search_key = request.GET.get('search[value]')  # 搜索关键字
    # order_column = request.GET.get('order[0][column]')  # 排序字段索引
    # order_column = request.GET.get('order[0][dir]')  # 排序规则：ase/desc

    search_options = {}
    try:
        if log_user:
            search_options.update({"username": {"$regex": f".*{log_user}.*"}})

        if log_path:
            search_options.update({"path": {"$regex": f".*{log_path}.*"}})

        if start_time and end_time:
            start_time = datetime.datetime.strptime(start_time, '%Y-%m-%d')
            end_time = datetime.datetime.strptime(end_time, '%Y-%m-%d') + datetime.timedelta(1)
            search_options.update({"datetime": {"$gt": start_time, "$lt": end_time}})

        searched_data, _ = mongo.find(search_options, start, length, sort_key='datetime', sort_method=-1)
        _, count = mongo.find(search_options)
        dic = {
            'draw': draw,
            'recordsFiltered': count,
            'recordsTotal': count,
            'data': searched_data
        }
        return HttpResponse(json.dumps(dic, cls=JSONEncoder), content_type='application/json')
    except Exception as e:
        return JsonResponse({'code': 500, 'data': None, 'msg': '获取失败：{}'.format(e)})
