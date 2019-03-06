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
from projs.models import DeployLog
from conf.logger import deploy_logger


@app.task
def deploy_log(project_config, deploy_user, d_type, branch_tag, release_name, release_desc, result):
    try:
        DeployLog.objects.create(
            project_config=project_config,
            deploy_user=deploy_user,
            d_type=d_type,
            branch_tag=branch_tag,
            release_name=release_name,
            release_desc=release_desc,
            result=result,
        )
    except Exception as e:
        deploy_logger.error('添加部署操作记录失败，原因：{}'.format(e))
