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
import json
import logging
from Ops.celery import app
from assets.models import AssetsLog
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
def admin_file(filename, txts, header=None):
    try:
        if header:
            f = open(filename, 'a')
            f.write(json.dumps(header) + '\n')
            for txt in txts:
                f.write(json.dumps(txt) + '\n')
            f.close()
        else:
            with open(filename, 'a') as f:
                for txt in txts:
                    f.write(txt)
    except Exception as e:
        logging.getLogger().error('添加用户操作记录文件失败，原因：{}'.format(e))
