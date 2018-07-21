# -*- coding: utf-8 -*-

from django.urls import path, re_path
from assets import views

urlpatterns = [
    path(r'assets_charts/', views.get_assets_charts, name='assets_charts'),
    path(r'assets_list/', views.get_assets_list, name='assets_list'),
    re_path(r'assets_search/(?P<key>(.*?))/', views.assets_search, name='assets_search'),
    path(r'add_asset/', views.add_asset, name='add_asset'),
    path(r'add_base_asset/', views.add_base_asset, name='add_base_asset'),
    re_path(r'update_asset/(?P<asset_type>(.*?))/(?P<pk>[0-9]+)/', views.update_asset, name='update_asset'),
    path(r'assets_log/', views.get_assets_log, name='assets_log'),
]
