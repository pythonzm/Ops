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
import subprocess
from channels.generic.websocket import WebsocketConsumer


class LogConsumer(WebsocketConsumer):

    def websocket_connect(self, event):
        self.accept()

    def websocket_receive(self, event):
        scan_info = json.loads(event['text'])
        cmd = "/usr/bin/ssh -p {port} {user}@{host} /usr/bin/tailf {log_file}".format(port=scan_info['port'],
                                                                                      user=scan_info['user'],
                                                                                      host=scan_info['host'],
                                                                                      log_file=scan_info['log_file'])
        popen = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        while True:
            line = popen.stdout.readline().strip()
            if line:
                self.send(json.dumps({'loginfo': line.decode('utf-8')}))

    def websocket_disconnect(self, event):
        self.send(json.dumps({
            "type": "websocket.send",
            "text": event["text"],
        }))
