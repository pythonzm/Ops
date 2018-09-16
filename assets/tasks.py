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
from assets.models import AssetsLog, SSHRecord
from conf.logger import user_logger


@app.task
def assets_record(user, remote_ip, content):
    try:
        AssetsLog.objects.create(
            user=user,
            remote_ip=remote_ip,
            content=content,
        )
    except Exception as e:
        user_logger.error('添加用户操作记录失败，原因：{}'.format(e))


@app.task
def ssh_record(ssh_login_user, ssh_server, ssh_remote_ip, ssh_start_time, ssh_login_status_time, ssh_record_file):
    try:
        SSHRecord.objects.create(
            ssh_login_user=ssh_login_user,
            ssh_server=ssh_server,
            ssh_remote_ip=ssh_remote_ip,
            ssh_start_time=ssh_start_time,
            ssh_login_status_time=ssh_login_status_time,
            ssh_record_file=ssh_record_file
        )
    except Exception as e:
        user_logger.error('添加登录管理用户操作记录失败，原因：{}'.format(e))