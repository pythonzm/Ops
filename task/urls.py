# -*- coding: utf-8 -*-
"""
-------------------------------------------------
   File Name：      urls
   Description:
   Author:          Administrator
   date：           2018/6/11
-------------------------------------------------
   Change Activity:
                    2018/6/11:
-------------------------------------------------
"""
from django.urls import path
from task import views

urlpatterns = [
    path(r'inventory/', views.gen_inventory, name='inventory'),
    path(r'run_module/', views.run_module, name='run_module'),
    path(r'run_log/', views.run_log, name='run_log'),
]
