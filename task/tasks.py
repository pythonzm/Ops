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
from task.models import AnsibleModuleLog, AnsiblePlaybookLog
from conf.logger import ansible_logger


@app.task
def module_record(ans_user, ans_remote_ip, ans_module, ans_args, ans_server, ans_result):
    try:
        AnsibleModuleLog.objects.create(
            ans_user=ans_user,
            ans_remote_ip=ans_remote_ip,
            ans_module=ans_module,
            ans_args=ans_args,
            ans_server=ans_server,
            ans_result=ans_result,
        )
    except Exception as e:
        ansible_logger.error('添加执行模块操作记录失败，原因：{}'.format(e))


@app.task
def playbook_record(playbook_user, playbook_remote_ip, playbook_name, playbook_result):
    try:
        AnsiblePlaybookLog.objects.create(
            playbook_user=playbook_user,
            playbook_remote_ip=playbook_remote_ip,
            playbook_name=playbook_name,
            playbook_result=playbook_result,
        )
    except Exception as e:
        ansible_logger.error('添加执行playbook操作记录失败，原因：{}'.format(e))
