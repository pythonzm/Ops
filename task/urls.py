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
    path(r'playbook_add/', views.playbook_add, name='playbook_add'),
    path(r'playbook_upload/', views.playbook_upload, name='playbook_upload'),
    path(r'playbook_list/', views.playbook_list, name='playbook_list'),
    re_path(r'role_detail/(?P<pk>[0-9]+)/', views.role_detail, name='role_detail'),
    path(r'role_list/', views.role_list, name='role_list'),
    path(r'role_edit/', views.role_edit, name='role_edit'),
    path(r'role_add/', views.role_add, name='role_add'),
    path(r'path_del/', views.path_del, name='path_del'),
    path(r'path_create/', views.path_create, name='path_create'),
    path(r'get_file_content/', views.get_file_content, name='get_file_content'),
    re_path(r'playbook_run/(?P<pk>[0-9]+)/', views.playbook_run, name='playbook_run'),
    re_path(r'playbook_info/(?P<pk>[0-9]+)/', views.playbook_info, name='playbook_info'),
    re_path(r'playbook_del/(?P<pk>[0-9]+)/', views.playbook_del, name='playbook_del'),
    re_path(r'role_del/(?P<pk>[0-9]+)/', views.role_del, name='role_del'),
    re_path(r'playbook_log_del/(?P<pk>[0-9]+)/', views.playbook_log_del, name='playbook_log_del'),
    re_path(r'module_log_del/(?P<pk>[0-9]+)/', views.module_log_del, name='module_log_del'),
    path(r'check_name/', views.check_name, name='check_name'),
    path(r'get_inventory_hosts/', views.get_inventory_hosts, name='get_inventory_hosts')
]
