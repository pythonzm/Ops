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
from django.urls import path, re_path
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from utils.log_websocket import LogConsumer
from utils.webssh_websocket import FortConsumer
from assets.utils.webssh import SSHConsumer

application = ProtocolTypeRouter({

    "websocket": AuthMiddlewareStack(
        URLRouter([
            # URLRouter just takes standard Django path() or url() entries.
            path(r'ws/log/', LogConsumer),
            re_path(r'ws/fortssh/([0-9]+)/([0-9]+)/(?P<group_name>.*)/', FortConsumer),
            re_path(r'ws/webssh/([0-9]+)/(?P<group_name>.*)/', SSHConsumer),
        ]),
    ),
})
