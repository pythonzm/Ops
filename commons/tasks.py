# -*- coding: utf-8 -*-
"""
-------------------------------------------------
   File Name：      tasks
   Description:
   Author:          Administrator
   date：           2019-07-05
-------------------------------------------------
   Change Activity:
                    2019-07-05:
-------------------------------------------------
"""
from __future__ import absolute_import, unicode_literals
import json
import requests
import datetime
from Ops.celery import app
from django.conf import settings
from utils.wx_alert import WxApi


@app.task
def get_login_info(login_user, login_ip, login_status):
    """
    获取登录登录信息
    :param login_user:
    :param login_ip:
    :param login_status:
    :return:
    """
    url = f'http://ip-api.com/json/{login_ip}?lang=zh-CN'
    r = requests.get(url=url)
    wx = WxApi('XXXXXXXXXXXXXXXXXXX', 'XXXXXXXXXXXXXXXXXXXXXXXXXXXXX')

    if r.status_code == 200:
        info = json.loads(r.text)
        if info.get('status') == 'fail':
            content = '用户{}于{}尝试登录系统\n结果：{}\n登录IP：{}\n'.format(login_user,
                                                               datetime.datetime.now().strftime(settings.TIME_FORMAT),
                                                               login_status, login_ip)
        else:
            content = '用户{}于{}尝试登录系统\n结果：{}\n登录IP：{}\n登录国家：{}\n登录省市：{}\n登录城市：{}\n'.format(login_user,
                                                                                          datetime.datetime.now().strftime(
                                                                                              settings.TIME_FORMAT),
                                                                                          login_status, login_ip,
                                                                                          info.get('country'),
                                                                                          info.get('regionName'),
                                                                                          info.get('city'))
    else:
        content = '用户{}于{}尝试登录系统\n结果：{}\n登录IP：{}\n'.format(login_user,
                                                           datetime.datetime.now().strftime(settings.TIME_FORMAT),
                                                           login_status, login_ip)
    wx.send_msg(subject='系统ops.juren.com登录提醒【重要】', content=content)
