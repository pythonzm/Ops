from django.contrib import admin

# Register your models here.
from scanhosts.models import HostInfo
from extra_apps import xadmin


class HostInfoAdmin():
    list_display = ('hostname', 'system_ver', 'sn', 'scan_datetime')


xadmin.site.register(HostInfo, HostInfoAdmin)
