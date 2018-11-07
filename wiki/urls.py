# -*- coding: utf-8 -*-

from django.urls import path, re_path, include
from wiki import views

urlpatterns = [
    path(r'wiki_add/', views.wiki_add, name='wiki_add'),
    path(r'upload_image/', views.upload_image, name='upload_image'),
    path(r'wiki_list/', views.wiki_list, name='wiki_list'),
    re_path(r'wiki_view/(?P<pk>[0-9]+)/', views.wiki_view, name='wiki_view'),
    re_path(r'wiki_edit/(?P<pk>[0-9]+)/', views.wiki_edit, name='wiki_edit'),
    path(r'wiki_search/', include('haystack.urls')),
    path(r'wiki_file_list', views.wiki_file_list, name='wiki_file_list'),
    re_path(r'wiki_file_del/(?P<pk>[0-9]+)/', views.wiki_file_del, name='wiki_file_del'),
    re_path(r'wiki_file_download/(?P<pk>[0-9]+)/', views.wiki_file_download, name='wiki_file_download'),
]
