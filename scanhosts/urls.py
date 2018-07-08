# -*- coding: utf-8 -*-

from django.urls import path, re_path
from scanhosts import views

urlpatterns = [
    path(r'result/', views.result, name='scan_result'),
    path(r'history', views.scan_history, name='scan_history'),
    re_path(r'detail/(?P<pk>[0-9]+)/', views.scan_detail, name='scan_detail'),
    path(r'test/', views.test, name='test'),
]
