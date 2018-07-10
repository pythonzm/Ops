# -*- coding: utf-8 -*-
from django.shortcuts import redirect
from django.utils.deprecation import MiddlewareMixin
from users.models import UserProfile


class UserLoginMiddleware(MiddlewareMixin):

    @staticmethod
    def process_request(request):
        # 若请求的是登陆页面 则往下执行
        if request.path == '/login/':
            return None
        user = request.session.get('username')
        if not user:
            return redirect('/login/')
