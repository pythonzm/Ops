# -*- coding: utf-8 -*-
"""
-------------------------------------------------
   File Name：      custom_tags
   Description:
   Author:          Administrator
   date：           2018-08-30
-------------------------------------------------
   Change Activity:
                    2018-08-30:
-------------------------------------------------
"""
import re
from django import template

register = template.Library()

re_ip = re.compile(
    r'^(10\.\d{1,3}\.\d{1,3}\.\d{1,3})|(172\.((1[6-9])|(2\d)|(3[01]))\.\d{1,3}\.\d{1,3})|(192\.168\.\d{1,3}\.\d{1,3})$')


@register.filter
def intranet_ip(ip):
    if re_ip.match(ip):
        return '<span class="label label-default">内</span>:{}'.format(ip)
    else:
        return '<span class="label label-info">外</span>:{}'.format(ip)


@register.filter
def get_file_name(name):
    return name.split('/')[-1]


@register.filter
def union_user_plan(self_plan, attention_plan):
    user_plans = self_plan | attention_plan
    plan_list = [user_plan for user_plan in user_plans if user_plan.status == 0]

    return plan_list


@register.filter
def user_plan_count(plan_list):
    return len(plan_list)
