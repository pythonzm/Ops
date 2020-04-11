# -*- coding: utf-8 -*-
"""
-------------------------------------------------
   File Name：      ssh
   Description:
   Author:          pythonzm
   date：           2019-11-05
-------------------------------------------------
   Change Activity:
                    2019-11-05:
-------------------------------------------------
"""
# -*- coding: utf-8 -*-

import time
import docker
import paramiko
import threading
from socket import timeout

from docker.models.containers import Container

from conf.logger import fort_logger
from django.http.request import QueryDict
from channels.generic.websocket import WebsocketConsumer


class MyThread(threading.Thread):
    def __init__(self, sock):
        super(MyThread, self).__init__()
        self.sock = sock
        self._stop_event = threading.Event()

    def stop(self):
        self._stop_event.set()

    def run(self):
        while not self._stop_event.is_set():
            try:
                data = self.sock.tty._sock.recv(1024)
                if data:
                    str_data = data.decode('utf-8', 'ignore')
                    self.sock.send(str_data)
                else:
                    return
            except timeout:
                break
        self.sock.send('\n由于长时间没有操作，连接已断开!', close=True)
        self.sock.close()


class DockerConsumer(WebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super(DockerConsumer, self).__init__(*args, **kwargs)
        self.client = docker.from_env()
        self.t1 = MyThread(self)
        # self.query = QueryDict(query_string=self.scope.get('query_string'), encoding='utf-8')
        # self.height = int(self.query.get('height'))
        # self.width = int(self.query.get('width'))
        self.tty = None

    def connect(self):
        if self.scope["user"].is_anonymous:
            self.close(code=1007)
        else:
            self.accept()

        try:
            resp = self.client.api.exec_create('ae89214140b5', cmd='/bin/bash', stdout=True, stderr=True, stdin=True,
                                               tty=True)

            self.tty = self.client.api.exec_start(
                resp['Id'], detach=False, tty=True, stream=False, socket=True
            )
        except Exception as e:
            self.send('通过web连接容器失败！原因：{}'.format(e), close=True)

        self.t1.setDaemon(True)
        self.t1.start()

    def receive(self, text_data=None, bytes_data=None):
        self.tty._sock.send(text_data.encode('utf-8'))

    def disconnect(self, close_code):
        self.client.close()
        self.t1.stop()
