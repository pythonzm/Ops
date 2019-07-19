# -*- coding: utf-8 -*-
"""
-------------------------------------------------
   File Name：      decorators
   Description:
   Author:          Administrator
   date：           2018-12-20
-------------------------------------------------
   Change Activity:
                    2018-12-20:
-------------------------------------------------
"""
from functools import wraps
from projs.models import ProjectConfig
from django.core.exceptions import PermissionDenied


def admin_auth(func):
    """
    验证用户是否是超级管理员
    """

    @wraps(func)
    def returned_wrapper(request, *args, **kwargs):
        if request.user.is_superuser:
            return func(request, *args, **kwargs)
        else:
            raise PermissionDenied

    return returned_wrapper


def deploy_auth(func):
    """
    验证用户是否对该项目有部署的权限
    """
    @wraps(func)
    def returned_wrapper(request, pk, *args, **kwargs):
        user = request.user
        projects = user.proj_admin.all() | user.proj_member.all()
        configs = ProjectConfig.objects.select_related('project').all() if user.is_superuser else \
            [project.projectconfig for project in projects if hasattr(project, 'projectconfig')]
        config = ProjectConfig.objects.get(id=pk)

        if config in configs:
            return func(request, pk, *args, **kwargs)
        else:
            raise PermissionDenied

    return returned_wrapper
