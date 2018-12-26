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
