"""Ops URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.urls import path, include, re_path
from django.views.static import serve
from django.conf import settings
from commons import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path(r'login/', views.login, name='login'),
    path(r'create_code/', views.gen_code_img, name='create_code'),
    path(r'logout/', views.logout, name='logout'),
    path(r'lock_screen/', views.lock_screen, name='lock_screen'),
    path(r'system_log/', views.system_log, name='system_log'),
    path(r'get_system_log/', views.get_system_log, name='get_system_log'),
    path(r'api/', include('api.urls')),
    path(r'run/', include('task.urls')),
    path(r'users/', include('users.urls')),
    path(r'assets/', include('assets.urls')),
    path(r'fort/', include('fort.urls')),
    path(r'project/', include('projs.urls')),
    path(r'plan/', include('plan.urls')),
    path(r'wiki/', include('wiki.urls')),
    path(r'db_config/', include('dbmanager.urls')),
    re_path(r'^media/(?P<path>.*)', serve, {"document_root": settings.MEDIA_ROOT}),
]
