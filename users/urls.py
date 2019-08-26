# -*- coding: utf-8 -*-

from django.urls import path, re_path
from users import views

urlpatterns = [
    path(r'user_list/', views.user_list, name='user_list'),
    path(r'get_user/', views.get_user, name='get_user'),
    path(r'group_list/', views.group_list, name='group_list'),
    path(r'get_group/', views.get_group, name='get_group'),
    path(r'user_role_list/', views.user_role_list, name='user_role_list'),
    path(r'get_user_role/', views.get_user_role, name='get_user_role'),
    path(r'create_plan/', views.create_plan, name='create_plan'),
    re_path(r'plan_info/(?P<pk>[0-9]+)/', views.plan_info, name='plan_info'),
    re_path(r'edit_user_role/(?P<pk>[0-9]+)/', views.edit_user_role, name='edit_user_role'),
    re_path(r'edit_group/(?P<pk>[0-9]+)/', views.edit_group, name='edit_group'),
    re_path(r'edit_user/(?P<pk>[0-9]+)/', views.edit_user, name='edit_user'),
    re_path(r'delete_user_role/(?P<pk>[0-9]+)/', views.delete_user_role, name='delete_user_role'),
    re_path(r'delete_group/(?P<pk>[0-9]+)/', views.delete_group, name='delete_group'),
    re_path(r'delete_user/(?P<pk>[0-9]+)/', views.delete_user, name='delete_user'),
    path(r'user_center/', views.user_center, name='user_center'),
    re_path(r'reset_password/(?P<pk>[0-9]+)/', views.reset_password, name='reset_password'),
]
