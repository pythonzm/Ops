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
from fort.models import FortRecord
from conf.logger import fort_logger


@app.task
def fort_record(login_user, fort, remote_ip, start_time, login_status_time, record_file):
    try:
        FortRecord.objects.create(
            login_user=login_user,
            fort=fort,
            remote_ip=remote_ip,
            start_time=start_time,
            login_status_time=login_status_time,
            record_file=record_file
        )
    except Exception as e:
        fort_logger.error('添加用户操作记录失败，原因：{}'.format(e))


@app.task
def test_celery(filename, some):
    with open(filename, 'a+') as f:
        f.write(some)
