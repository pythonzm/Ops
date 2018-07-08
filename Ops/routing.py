# -*- coding: utf-8 -*-
"""
-------------------------------------------------
   File Name：      routing
   Description:
   Author:          Administrator
   date：           2018/6/6
-------------------------------------------------
   Change Activity:
                    2018/6/6:
-------------------------------------------------
"""
from django.urls import path
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from utils.log_websocket import LogConsumer

application = ProtocolTypeRouter({

    "websocket": AuthMiddlewareStack(
        URLRouter([
            # URLRouter just takes standard Django path() or url() entries.
            path(r'ws/log/', LogConsumer),
        ]),
    ),
})

