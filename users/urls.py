# -*- coding: utf-8 -*-

from django.urls import path, re_path
from users import views

urlpatterns = [
    path(r'user_list/', views.get_user_list, name='user_list'),
    path(r'group_list/', views.get_group_list, name='group_list'),
    re_path(r'user/(?P<pk>[0-9]+)', views.get_user_detail, name='user_detail'),
    re_path(r'group/(?P<pk>[0-9]+)', views.get_group_detail, name='group_detail'),
    path(r'create_user', views.create_user, name='create_user'),
    path(r'user_center', views.user_center, name='user_center'),
    re_path(r'reset_password/(?P<pk>[0-9]+)', views.reset_password, name='reset_password'),
    path(r'user_log', views.get_user_log, name='user_log'),
    path(r'del_user_plan', views.del_user_plan, name='del_user_plan'),
    re_path(r'update_user_plan/(.*)', views.update_user_plan, name='update_user_plan'),
]
