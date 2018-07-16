# -*- coding: utf-8 -*-
from django.shortcuts import redirect
from django.utils.deprecation import MiddlewareMixin
from users.tasks import users_record
from users.models import UserProfile
from django.contrib.auth.models import Group


class UserLoginMiddleware(MiddlewareMixin):
    @staticmethod
    def process_request(request):
        # 若请求的是登陆页面 则往下执行
        if request.path == '/login/' or request.path == '/lock_screen/':
            return None
        else:
            user = request.session.get('username')
            lock = request.session.get('lock')
            if not user:
                return redirect('/login/')
            if lock:
                return redirect('/lock_screen/')


class RecordMiddleware(MiddlewareMixin):
    def process_request(self, request):
        if request.method == 'DELETE' or request.method == 'delete':
            if 'users' in request.path:
                user_id = self.get_id(request.path)
                username = UserProfile.objects.get(id=user_id).username
                users_record.delay(user=request.user, remote_ip=request.META['REMOTE_ADDR'],
                                   content='删除用户：{}'.format(username))
            elif 'group' in request.path:
                group_id = self.get_id(request.path)
                groupname = Group.objects.get(id=group_id).name
                users_record.delay(user=request.user, remote_ip=request.META['REMOTE_ADDR'],
                                   content='删除用户组：{}'.format(groupname))

        elif request.method == 'PUT' or request.method == 'put':
            if r'users' in request.path:
                user_id = self.get_id(request.path)
                username = UserProfile.objects.get(id=user_id).username
                users_record.delay(user=request.user, remote_ip=request.META['REMOTE_ADDR'],
                                   content='修改用户：{}'.format(username))
            elif 'group' in request.path:
                group_id = self.get_id(request.path)
                groupname = Group.objects.get(id=group_id).name
                users_record.delay(user=request.user, remote_ip=request.META['REMOTE_ADDR'],
                                   content='修改用户组：{}'.format(groupname))

        elif request.method == 'POST' or request.method == 'post':
            if 'create_user' in request.path:
                users_record.delay(user=request.user, remote_ip=request.META['REMOTE_ADDR'],
                                   content='创建用户：{}'.format(request.POST.get('username')))
            elif 'group' in request.path:
                body = str(request.__dict__.get('_body'), encoding="utf-8")
                name = eval(body)['name']
                users_record.delay(user=request.user, remote_ip=request.META['REMOTE_ADDR'],
                                   content='创建用户组：{}'.format(name))
        return None

    @staticmethod
    def get_id(path):
        if path.endswith('/'):
            pk = path.split('/')[-2]
        else:
            pk = path.split('/')[-1]
        return pk
