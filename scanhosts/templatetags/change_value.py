# -*- coding: utf-8 -*-
"""
-------------------------------------------------
   File Name：      change_value
   Description:
   Author:          Administrator
   date：           2018/6/11
-------------------------------------------------
   Change Activity:
                    2018/6/11:
-------------------------------------------------
"""
from django import template
from scanhosts.models import HostInfo
from utils.get_verbose_name import get_model_fields

register = template.Library()


@register.filter
def change_value(value, k):
    for i in get_model_fields(HostInfo):
        if i == k:
            return '{}.{}'.format(value, i)
