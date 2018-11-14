# -*- coding: utf-8 -*-
"""
-------------------------------------------------
   File Name：      urls
   Description:
   Author:          Administrator
   date：           2018/6/11
-------------------------------------------------
   Change Activity:
                    2018/6/11:
-------------------------------------------------
"""
from django.urls import path, re_path
from task import views

urlpatterns = [
    path(r'inventory/', views.gen_inventory, name='inventory'),
    path(r'run_module/', views.run_module, name='run_module'),
    path(r'run_log/', views.run_log, name='run_log'),
    path(r'run_playbook_online/', views.run_playbook_online, name='run_playbook_online'),
    path(r'playbook_upload/', views.playbook_upload, name='playbook_upload'),
    path(r'playbook_list/', views.playbook_list, name='playbook_list'),
    re_path(r'playbook_run/(?P<pk>[0-9]+)/', views.playbook_run, name='playbook_run'),
    re_path(r'playbook_info/(?P<pk>[0-9]+)/', views.playbook_info, name='playbook_info'),
    re_path(r'playbook_del/(?P<pk>[0-9]+)/', views.playbook_del, name='playbook_del'),
    re_path(r'playbook_log_del/(?P<pk>[0-9]+)/', views.playbook_log_del, name='playbook_log_del'),
    re_path(r'module_log_del/(?P<pk>[0-9]+)/', views.module_log_del, name='module_log_del'),
    path(r'chk_playbook_name/', views.check_playbook_name, name='chk_playbook_name'),
    path(r'get_inventory_hosts/', views.get_inventory_hosts, name='get_inventory_hosts')
]
