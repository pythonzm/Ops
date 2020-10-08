# -*- coding: utf-8 -*-
"""
-------------------------------------------------
   File Name：      routing
   Description:
   Author:          pythonzm
   date：           2018/6/6
-------------------------------------------------
   Change Activity:
                    2018/6/6:
-------------------------------------------------
"""
from django.urls import path, re_path
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from projs.utils.log_websocket import LogConsumer
from fort.utils.webssh import FortConsumer
from assets.utils.webssh import SSHConsumer
from fort.utils.webguacamole import GuacamoleConsumer
from assets.utils.webguacamole import AdminGuacamole
from task.utils.ans_module_websocket import AnsModuleConsumer
from task.utils.ans_playbook_websocket import AnsPlaybookConsumer
from projs.utils.deploy_websocket import DeployConsumer

application = ProtocolTypeRouter({

    "websocket": AuthMiddlewareStack(
        URLRouter([
            # URLRouter just takes standard Django path() or url() entries.
            path(r'ws/deploy/', DeployConsumer),
            path(r'ws/ans_module_log/', AnsModuleConsumer),
            path(r'ws/ans_playbook_log/', AnsPlaybookConsumer),
            path(r'ws/deploy_log/', LogConsumer),
            re_path(r'ws/fortssh/([0-9]+)/([0-9]+)/', FortConsumer),
            re_path(r'ws/webssh/([0-9]+)/', SSHConsumer),
            re_path(r'ws/fort_guacamole/([0-9]+)/([0-9]+)/(?P<group_name>.*)/', GuacamoleConsumer),
            re_path(r'ws/admin_guacamole/([0-9]+)/(?P<group_name>.*)/', AdminGuacamole),
        ]),
    ),
})
