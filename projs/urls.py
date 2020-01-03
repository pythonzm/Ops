# -*- coding: utf-8 -*-

from django.urls import path, re_path
from projs import views

urlpatterns = [
    path(r'auto_deploy/', views.auto_deploy, name='auto_deploy'),
    path(r'proj_list/', views.proj_list, name='proj_list'),
    path(r'proj_config/', views.proj_config, name='proj_config'),
    path(r'config_list/', views.config_list, name='config_list'),
    path(r'deploy_log/', views.deploy_log, name='deploy_log'),
    re_path(r'check_log/(?P<pk>[0-9]+)/', views.check_log, name='check_log'),
    re_path(r'deploy/(?P<pk>[0-9]+)/', views.deploy, name='deploy'),
    re_path(r'rollback/(?P<pk>[0-9]+)/', views.deploy, name='rollback'),
    re_path(r'proj_list/(?P<pk>[0-9]+)/', views.proj_org, name='proj_org'),
    re_path(r'org_chart/(?P<pk>[0-9]+)/', views.org_chart, name='org_chart'),
]
