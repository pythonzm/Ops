# -*- coding: utf-8 -*-
from django.shortcuts import redirect
from django.utils.deprecation import MiddlewareMixin
from users.tasks import users_record
from assets.tasks import assets_record
from task.tasks import module_record, playbook_record
from users.models import UserProfile
from django.contrib.auth.models import Group
from assets.models import Assets, ServerAssets


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
            elif 'group' in request.path:
                body = str(request.__dict__.get('_body'), encoding="utf-8")
                name = eval(body)['name']
                users_record.delay(user=request.user, remote_ip=request.META['REMOTE_ADDR'],
                                   content='创建用户组：{}'.format(name))
            elif 'api' in request.path and '_assets/' in request.path:
                body = str(request.__dict__.get('_body'), encoding="utf-8")
                asset_nu = eval(body)['assets']['asset_nu']
                assets_record.delay(user=request.user, remote_ip=request.META['REMOTE_ADDR'],
                                    content='新增资产，资产编号为：{}'.format(asset_nu))

    @staticmethod
    def process_response(request, response):
        if request.method == 'POST' and 'run_module' in request.path and response.status_code == 200:
            post_data = dict(request._post)
            ans_server = [ServerAssets.objects.get(id=host_id).assets.asset_management_ip for host_id in
                          post_data['ans_group_hosts']]
            response_data = str(response.__dict__.get('_container')[0], encoding="utf-8")
            res = eval(response_data)['msg']
            module_record.delay(ans_user=request.user, ans_remote_ip=request.META['REMOTE_ADDR'],
                                ans_module=''.join(post_data['ansibleModule']) if
                                post_data['ansibleModule'] != ['custom'] else ''.join(post_data['customModule']),
                                ans_args=''.join(post_data['ansibleModuleArgs']),
                                ans_server=ans_server, ans_result=res)
        elif request.method == 'POST' and (
                'playbook_run' in request.path or 'role_run' in request.path) and response.status_code == 200:
            playbook_name = dict(request._post).get('playbook_name')[0]
            response_data = str(response.__dict__.get('_container')[0], encoding="utf-8")
            res = eval(response_data)['msg']

            playbook_record.delay(
                playbook_user=request.user,
                playbook_remote_ip=request.META['REMOTE_ADDR'],
                playbook_name=playbook_name,
                playbook_result=res
            )
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
