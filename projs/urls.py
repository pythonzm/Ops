# -*- coding: utf-8 -*-

from django.urls import path, re_path
from projs import views

urlpatterns = [
    path(r'proj_list/', views.proj_list, name='proj_list'),
    re_path(r'proj_list/(?P<pk>[0-9]+)/', views.proj_org, name='proj_org'),
    re_path(r'org_chart/(?P<pk>[0-9]+)/', views.org_chart, name='org_chart'),
]
