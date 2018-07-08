# -*- coding: utf-8 -*-
"""
-------------------------------------------------
   File Name：      asgi
   Description:
   Author:          Administrator
   date：           2018/6/6
-------------------------------------------------
   Change Activity:
                    2018/6/6:
-------------------------------------------------
"""
import os
import django
from channels.routing import get_default_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "Ops.settings")
django.setup()
application = get_default_application()
