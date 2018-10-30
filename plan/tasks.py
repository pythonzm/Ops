# -*- coding: utf-8 -*-
"""
-------------------------------------------------
   File Name：      tasks
   Description:
   Author:          Administrator
   date：           2018-07-16
-------------------------------------------------
   Change Activity:
                    2018-07-16:
-------------------------------------------------
"""
from __future__ import absolute_import, unicode_literals
from Ops.celery import app
from assets.utils.zabbix_api import ZabbixApi
from Ops import settings
from assets.models import ZabbixAlert
import datetime


@app.task
def test_celery(filename, some):
    with open(filename, 'a+') as f:
        f.write(some)


@app.task
def get_zabbix_alert():
    """
    每天获取zabbix当天的告警总数
    :return:
    """
    alerts = []
    zabbix_api = ZabbixApi(settings.ZABBIX_INFO['api_url'], settings.ZABBIX_INFO['username'],
                           settings.ZABBIX_INFO['password'])
    zabbix_api.login()
    res = zabbix_api.get_alerts()

    today = datetime.date.today()

    for i in res:
        if '不好' in i.get('subject') and datetime.date.fromtimestamp(int(i.get('clock'))) == today:
            alerts.append(i)

    ZabbixAlert.objects.create(alert_num=len(alerts))
