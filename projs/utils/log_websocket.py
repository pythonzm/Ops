# -*- coding: utf-8 -*-
"""
-------------------------------------------------
   File Name：      consumers
   Description:
   Author:          Administrator
   date：           2018/6/6
-------------------------------------------------
   Change Activity:
                    2018/6/6:
-------------------------------------------------
"""
import json
import time
import threading
import subprocess
from utils.crypt_pwd import CryptPwd
from channels.generic.websocket import WebsocketConsumer


class MyThread(threading.Thread):
    def __init__(self, chan):
        super(MyThread, self).__init__()
        self.chan = chan
        self._stop_event = threading.Event()

    def stop(self):
        self._stop_event.set()

    def run(self):
        popen = subprocess.Popen(self.chan.cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        while not self._stop_event.is_set():
            time.sleep(0.1)
            line = popen.stdout.readline().strip()
            if line:
                self.chan.send(line.decode('utf-8'))


class LogConsumer(WebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super(LogConsumer, self).__init__(*args, **kwargs)
        self.host = None
        self.port = None
        self.username = None
        self.password = None
        self.log_file = None
        self.cmd = None
        self.t1 = MyThread(self)

    def connect(self):
        if self.scope["user"].is_anonymous:
            self.close(code=1007)
        else:
            self.accept()

    def receive(self, text_data=None, bytes_data=None):
        info = json.loads(text_data)
        self.host = info['host']
        self.port = info['port']
        self.username = info['username']
        self.password = CryptPwd().decrypt_pwd(info['password'])
        self.log_file = info['log_file']

        self.cmd = "/usr/bin/sshpass -p {password} /usr/bin/ssh -t -p {port} {user}@{host} /usr/bin/tailf " \
                   "{log_file}".format(password=self.password, port=self.port, user=self.username, host=self.host,
                                       log_file=self.log_file)

        self.t1.setDaemon(True)
        self.t1.start()

    def disconnect(self, close_code):
        cmd = "/usr/bin/sshpass -p {password} /usr/bin/ssh -t -p {port} {user}@{host} /usr/bin/pkill tailf".format(
            password=self.password, port=self.port, user=self.username, host=self.host)
        try:
            subprocess.getoutput(cmd)
        finally:
            self.t1.stop()
