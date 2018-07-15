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
from django.contrib import admin
from django.urls import path, include, re_path
from django.views.static import serve
from Ops.settings import MEDIA_ROOT
from Ops import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.dashboard, name='dashboard'),
    path('login/', views.login, name='login'),
    path('logout/', views.logout, name='logout'),
    path('lock_screen', views.lock_screen, name='lock_screen'),
    path(r'api/', include('api.urls')),
    path(r'scan_host/', include('scanhosts.urls')),
    path(r'run/', include('ansible_task.urls')),
    path(r'users/', include('users.urls')),
    path(r'assets/', include('assets.urls')),
    re_path(r'^media/(?P<path>.*)', serve, {"document_root": MEDIA_ROOT}),
]
