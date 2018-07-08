# -*- coding: utf-8 -*-

from django.urls import path, re_path
from users import views

urlpatterns = [
    path(r'user_list/', views.get_user_list, name='user_list'),
    re_path(r'user/(?P<pk>[0-9]+)', views.get_user_detail, name='user_detail'),
    path(r'create_user', views.create_user, name='create_user'),
    path(r'user_center', views.user_center, name='user_center'),
]
