# -*- coding: utf-8 -*-
"""
-------------------------------------------------
   File Name：      webssh_websocket
   Description:
   Author:          Administrator
   date：           2018-08-07
-------------------------------------------------
   Change Activity:
                    2018-08-07:
-------------------------------------------------
"""
from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer

import paramiko
import threading
import time
import json

from channels.layers import get_channel_layer

channel_layer = get_channel_layer()


class MyThread(threading.Thread):
    def __init__(self, nu, chan):
        threading.Thread.__init__(self)
        self.chan = chan
        self.nu = nu

    def run(self):
        while not self.chan.chan.exit_status_ready():
            time.sleep(0.1)
            try:
                data = self.chan.chan.recv(1024)
                async_to_sync(self.chan.channel_layer.group_send)(
                    self.chan.scope['user'].username,
                    {
                        "type": "user.message",
                        "text": bytes.decode(data)
                    },
                )
            except Exception as ex:
                print(str(ex))
        self.chan.sshclient.close()
        return False


class SSHConsumer(WebsocketConsumer):

    def __init__(self, *args, **kwargs):
        super(SSHConsumer, self).__init__(*args, **kwargs)
        self.sshclient = paramiko.SSHClient()

    def websocket_connect(self, event):
        # 创建channels group， 命名为：用户名，并使用channel_layer写入到redis
        async_to_sync(self.channel_layer.group_add)(self.scope['user'].username, self.channel_name)
        # 返回给receive方法处理
        self.accept()

    def websocket_receive(self, event):
        ssh_info = json.loads(event['text'])
        self.sshclient.load_system_host_keys()
        self.sshclient.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.sshclient.connect(ssh_info['host'], int(ssh_info['post']), ssh_info['username'], ssh_info['password'])
        self.chan = self.sshclient.invoke_shell(term='xterm')
        self.chan.settimeout(0)
        t1 = MyThread(999, self)
        t1.setDaemon(True)
        t1.start()

    def websocket_disconnect(self, event):
        async_to_sync(self.channel_layer.group_discard)(self.scope['user'].username, self.channel_name)
        self.send(json.dumps({
            "type": "websocket.send",
            "text": event["text"],
        }))
