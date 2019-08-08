# -*- coding: utf-8 -*-

from django.urls import path, re_path
from dbmanager import views

urlpatterns = [
    path(r'db_list/', views.db_list, name='db_list'),
    path(r'db_user/', views.db_user, name='db_user'),
    re_path(r'db_edit/(?P<pk>[0-9]+)/', views.db_edit, name='db_edit'),
    re_path(r'db_del/(?P<pk>[0-9]+)/', views.db_del, name='db_del'),
    path(r'db_exec/', views.db_exec, name='db_exec'),
    path(r'db_log/', views.db_log, name='db_log'),
    re_path(r'db_log_detail/', views.db_log_detail, name='db_log_detail'),
]
