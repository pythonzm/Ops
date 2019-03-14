# -*- coding: utf-8 -*-
"""
-------------------------------------------------
   File Name：      deploy_notice
   Description:
   Author:          Administrator
   date：           2019-03-14
-------------------------------------------------
   Change Activity:
                    2019-03-14:
-------------------------------------------------
"""
from django.core.mail.message import EmailMultiAlternatives


def deploy_mail():
    msg = EmailMultiAlternatives('subject', 'hello', to=['794573172@qq.com'], cc=['zmshijie0@163.com'])
    msg.send()
