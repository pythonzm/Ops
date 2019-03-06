# -*- coding: utf-8 -*-
from django.shortcuts import redirect
from django.utils.deprecation import MiddlewareMixin
from users.tasks import users_record
from assets.tasks import assets_record
from users.models import UserProfile
from django.contrib.auth.models import Group
from assets.models import Assets


class UserLoginMiddleware(MiddlewareMixin):
    @staticmethod
    def process_request(request):
        # 若请求的是登陆页面 则往下执行
        if request.path not in ['/login/', '/logout/', '/lock_screen/', '/create_code/']:
            user = request.session.get('username')
            lock = request.session.get('lock')
            if not user:
                return redirect('/login/?next={}'.format(request.path))
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
            elif 'assets' in request.path and 'log' not in request.path:
                asset_id = self.get_id(request.path)
                asset_nu = Assets.objects.get(id=asset_id).asset_nu
                assets_record.delay(user=request.user, remote_ip=request.META['REMOTE_ADDR'],
                                    content='删除资产，资产编号为：{}'.format(asset_nu))

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
            elif r'/api/assets' in request.path:
                asset_id = self.get_id(request.path)
                asset_nu = Assets.objects.get(id=asset_id).asset_nu
                assets_record.delay(user=request.user, remote_ip=request.META['REMOTE_ADDR'],
                                    content='修改资产，资产编号为：{}'.format(asset_nu))

        elif request.method == 'POST' or request.method == 'post':
            if 'create_user' in request.path:
                users_record.delay(user=request.user, remote_ip=request.META['REMOTE_ADDR'],
                                   content='创建用户：{}'.format(request.POST.get('username')))

    @staticmethod
    def process_response(request, response):
        if 'api' in request.path and '_assets/' in request.path and response.status_code == 201:
            res = dict(response.__dict__.get('data').get('assets'))
            assets_record.delay(user=request.user, remote_ip=request.META['REMOTE_ADDR'],
                                content='新增资产，资产编号为：{}'.format(res.get('asset_nu')))
        elif 'group' in request.path and response.status_code == 201:
            users_record.delay(user=request.user, remote_ip=request.META['REMOTE_ADDR'],
                               content='创建用户组：{}'.format(response.__dict__.get('data').get('name')))
        elif request.method == 'GET' and response.status_code == 200:
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
        return response

    @staticmethod
    def get_id(path):
        if path.endswith('/'):
            pk = path.split('/')[-2]
        else:
            pk = path.split('/')[-1]
        return pk
