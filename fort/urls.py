# -*- coding: utf-8 -*-

from django.urls import path, re_path
from fort import views

urlpatterns = [
    path(r'fort_server/', views.fort_server, name='fort_server'),
    path(r'ssh_list/', views.ssh_list, name='ssh_list'),
    re_path(r'terminal/(?P<server_id>[0-9]+)/(?P<fort_user_id>[0-9]+)/', views.terminal, name='terminal'),
    path(r'login_fort_record/', views.login_fort_record, name='login_fort_record'),
    re_path(r'record_play/(?P<pk>[0-9]+)/', views.record_play, name='record_play'),
]
