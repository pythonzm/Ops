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
    re_path(r'get_host_graph/(?P<pk>[0-9]+)/', views.get_host_graph, name='get_host_graph'),
    path(r'server_facts/', views.server_facts, name='server_facts'),
    re_path(r'get_server_info/(?P<pk>[0-9]+)/', views.get_asset_info, name='get_asset_info'),
    path(r'import_assets/', views.import_assets, name='import_assets'),
    re_path(r'export_assets/', views.export_assets, name='export_assets'),
    re_path(r'ssh/(?P<pk>[0-9]+)/', views.ssh_terminal, name='ssh'),
    path(r'login_ssh_record/', views.login_ssh_record, name='login_ssh_record'),
    re_path(r'ssh_play/(?P<pk>[0-9]+)/', views.ssh_play, name='ssh_play'),
]
