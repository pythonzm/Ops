# -*- coding: utf-8 -*-
import json
import datetime
from django.conf import settings
from users.models import UserProfile
from django.shortcuts import redirect
from utils.db.mongo_ops import MongoOps
from django.utils.deprecation import MiddlewareMixin

pass_paths = ['/login/', '/logout/', '/lock_screen/', '/create_code/', '/project/auto_deploy/']  # 指定哪些路径不保存所有用户列表的session
pass_keys = ['log', 'lock_screen', 'wiki', 'post', 'role_detail', 'assets/ssh', 'fort/terminal',
             'proj_list', 'user_center', 'db_exec']  # 指定哪些路径的非get请求不进行记录


class UserLoginMiddleware(MiddlewareMixin):
    @staticmethod
    def process_request(request):
        # 若请求的是登陆页面 则往下执行
        if request.path not in pass_paths:
            user = request.session.get('username')
            lock = request.session.get('lock')
            if not user:
                return redirect('/login/?next={}'.format(request.path))
            if lock:
                return redirect('/lock_screen/')


class RecordMiddleware(MiddlewareMixin):
    def __init__(self, *args, **kwargs):
        super(RecordMiddleware, self).__init__(*args, **kwargs)
        self.body = None
        self.mongo = MongoOps(settings.MONGODB_HOST, settings.MONGODB_PORT, settings.RECORD_DB, settings.RECORD_COLL)

    def process_request(self, request):
        if request.POST:
            self.body = {k: v[0] if len(v) == 1 else v for k, v in request.POST.lists()}
        else:
            self.body = getattr(request, '_body', request.body)

    def process_response(self, request, response):
        if request.method == 'GET' and request.path not in pass_paths and response.status_code == 200:
            user_infos = []
            users = UserProfile.objects.all()
            for user in users:
                user_info = {
                    'user_id': user.id,
                    'username': user.username,
                    'user_image': str(user.image),
                    'login_status': user.login_status
                }
                user_infos.append(user_info)
            request.session['user_infos'] = user_infos

        elif request.method != 'GET' and all([key not in request.path for key in pass_keys]):
            if isinstance(self.body, dict):
                data = self.body
            elif isinstance(self.body, bytes) and len(self.body) != 0:
                data = json.loads(self.body.decode('utf-8'))
            else:
                data = None

            if 'api' in request.path:
                code = response.status_code
            elif '_container' in response.__dict__:
                code = json.loads(response.__dict__.get('_container')[0].decode('utf-8')).get('code')
            else:
                code = None

            if data and 'action' in data and 'show' in data.get('action'):
                pass
            else:
                request_data = {'username': request.user.username, 'path': request.path, 'method': request.method,
                                'request_data': data, 'code': code,
                                'ip': request.META['REMOTE_ADDR'], 'datetime': datetime.datetime.now()}
                self.mongo.insert_one(request_data)
        return response
