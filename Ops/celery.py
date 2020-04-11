# -*- coding: utf-8 -*-
"""
-------------------------------------------------
   File Name：      celery
   Description:
   Author:          Administrator
   date：           2018-07-16
-------------------------------------------------
   Change Activity:
                    2018-07-16:
-------------------------------------------------
"""
import os
from celery import Celery
from kombu import Queue, Exchange

# set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Ops.settings')

app = Celery('Ops', broker='redis://127.0.0.1:7779/0')

app.conf.task_queues = (
    Queue('default', Exchange('default', type='direct'), routing_key='default'),
    Queue('ansible', Exchange('ansible', type='direct'), routing_key='ansible'),
    Queue('fort', Exchange('fort', type='direct'), routing_key='fort'),
    Queue('plan', Exchange('plan', type='direct'), routing_key='plan'),
    Queue('commons', Exchange('commons', type='direct'), routing_key='commons'),
)

app.conf.task_default_queue = 'default'
app.conf.task_default_exchange = 'default'
app.conf.task_default_exchange_type = 'direct'
app.conf.task_default_routing_key = 'default'
app.conf.timezone = 'Asia/Shanghai'
app.conf.enable_utc = False

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django app configs.
app.autodiscover_tasks()
