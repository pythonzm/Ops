# -*- coding: utf-8 -*-

from django.urls import path, re_path
from plan import views

urlpatterns = [
    path(r'schedule_list/', views.schedule_list, name='schedule_list'),
    path(r'add_crontab_schedule/', views.add_crontab_schedule, name='add_crontab_schedule'),
    path(r'add_interval_schedule/', views.add_interval_schedule, name='add_interval_schedule'),
    re_path(r'del_schedule/(?P<pk>[0-9]+)/', views.del_schedule, name='del_schedule'),
    path(r'task_list/', views.task_list, name='task_list'),
    path(r'task_result/', views.task_result, name='task_result')
]
