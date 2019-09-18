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
from utils.wx_alert import WxApi
from utils.db.mongo_ops import MongoOps
from Ops import settings
from assets.models import ZabbixAlert, Assets
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
        if '不好' in i.get('subject') and i.get('sendto') == '1' and datetime.date.fromtimestamp(
                int(i.get('clock'))) == today:
            alerts.append(i)

    ZabbixAlert.objects.create(alert_num=len(alerts))


@app.task
def get_expire_assets():
    """
    每天检测资产到期日期，如果距离到期日期小于等于30天，则微信报警
    :return:
    """
    assets = Assets.objects.all()
    expire_assets = []
    for asset in assets:
        expire_days = (asset.asset_expire_day - datetime.date.today()).days
        if 0 < expire_days <= 30:
            expire_assets.append(
                {'asset_type': asset.get_asset_type_display(), 'asset_nu': asset.asset_nu,
                 'asset_ip': asset.asset_management_ip, 'asset_expire': asset.asset_expire_day,
                 'expire_days': expire_days})

    if len(expire_assets) > 0:
        asset_details = [
            '{} -> 资产编号：{}\n IP地址 -> {} \n 距离到期日 {} 还剩{}天\n'.format(expire_asset.get('asset_type'),
                                                                    expire_asset.get('asset_nu'),
                                                                    expire_asset.get('asset_ip'),
                                                                    expire_asset.get('asset_expire'),
                                                                    expire_asset.get('expire_days'))
            for expire_asset in expire_assets]
        content = '共有{}个资产即将到期: \n{}'.format(len(asset_details), ' '.join(asset_details))

        wx = WxApi('XXXXXXXXXXXXXXXXX', 'XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX')

        wx.send_msg(subject='资产即将过期提醒【重要】', content=content)


@app.task
def remove_system_log(days=90):
    deadline = datetime.datetime.now() - datetime.timedelta(days)

    m = MongoOps(settings.MONGODB_HOST, settings.MONGODB_PORT, settings.RECORD_DB, settings.RECORD_COLL,
                 settings.MONGODB_USER, settings.MONGODB_PASS)
    rs, _ = m.find({"datetime": {"$lt": deadline}})
    m.delete({"datetime": {"$lt": deadline}}, del_all=True)
