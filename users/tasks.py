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
from users.models import UserLog
from conf.logger import user_logger


@app.task
def users_record(user, remote_ip, content):
    try:
        UserLog.objects.create(
            user=user,
            remote_ip=remote_ip,
            content=content,
        )
    except Exception as e:
        user_logger.error('添加用户操作记录失败，原因：{}'.format(e))
