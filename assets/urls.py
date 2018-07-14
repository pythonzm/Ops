# -*- coding: utf-8 -*-

from django.urls import path, re_path
from assets import views

urlpatterns = [
    path(r'assets_charts/', views.get_assets_charts, name='assets_charts'),
]
