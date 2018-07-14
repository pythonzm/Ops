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
        if request.path == '/login/':
            return None
        user = request.session.get('username')
        if not user:
            return redirect('/login/')


class RecordMiddleware(MiddlewareMixin):
    def process_request(self, request):
        if request.method == 'DELETE' or request.method == 'delete':
            if r'/api/users/' in request.path:
                user_id = self.get_id(request.path)
                username = UserProfile.objects.get(id=user_id).username
                users_record.delay(user=request.user, remote_ip=request.META['REMOTE_ADDR'],
                                   content='删除用户：{}'.format(username))
            elif r'/api/group/' in request.path:
                group_id = self.get_id(request.path)
                groupname = Group.objects.get(id=group_id).name
                users_record.delay(user=request.user, remote_ip=request.META['REMOTE_ADDR'],
                                   content='删除用户组：{}'.format(groupname))
            return None

    @staticmethod
    def process_response(request, response):
        if str(response.status_code).startswith('2'):
            if request.method == 'POST' or request.method == 'post':
                if 'create_user' in request.path:
                    users_record.delay(user=request.user, remote_ip=request.META['REMOTE_ADDR'],
                                       content='创建用户：{}'.format(request.POST.get('username')))
                elif r'/users/user/' in request.path:
                    users_record.delay(user=request.user, remote_ip=request.META['REMOTE_ADDR'],
                                       content='修改用户：{}'.format(request.POST.get('username')))
                elif 'create_group' in request.path:
                    users_record.delay(user=request.user, remote_ip=request.META['REMOTE_ADDR'],
                                       content='创建用户组：{}'.format(request.POST.get('groupname')))
                elif r'/users/group/' in request.path:
                    users_record.delay(user=request.user, remote_ip=request.META['REMOTE_ADDR'],
                                       content='修改用户组：{}'.format(request.POST.get('groupname')))
            elif request.method == 'PUT' or request.method == 'put':
                pass

            return response
        return response

    @staticmethod
    def get_id(path):
        if path.endswith('/'):
            pk = path.split('/')[-2]
        else:
            pk = path.split('/')[-1]
        return pk
