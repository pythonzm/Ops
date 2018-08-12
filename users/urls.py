# -*- coding: utf-8 -*-

from django.urls import path, re_path
from users import views

urlpatterns = [
    path(r'user_list/', views.get_user_list, name='user_list'),
    path(r'group_list/', views.get_group_list, name='group_list'),
    path(r'create_user/', views.create_user, name='create_user'),
    path(r'user_center/', views.user_center, name='user_center'),
    re_path(r'reset_password/(?P<pk>[0-9]+)/', views.reset_password, name='reset_password'),
    path(r'user_log/', views.get_user_log, name='user_log'),
    path(r'del_user_plan/', views.del_user_plan, name='del_user_plan'),
]
