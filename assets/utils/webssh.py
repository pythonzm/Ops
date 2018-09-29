# -*- coding: utf-8 -*-
import paramiko
import threading
import time
import os
import json
from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer
from assets.models import ServerAssets
from Ops import settings
from assets.tasks import ssh_record
from utils.crypt_pwd import CryptPwd


class MyThread(threading.Thread):
    def __init__(self, chan):
        super(MyThread, self).__init__()
        self.chan = chan

    def run(self):
        start_time = time.time()
        stdout = []
        current_time = time.strftime(settings.TIME_FORMAT)
        while not self.chan.chan.exit_status_ready():
            try:
                data = self.chan.chan.recv(1024)
                if data:
                    str_data = bytes.decode(data)
                    self.send_msg(str_data)
                    stdout.append([time.time() - start_time, 'o', str_data])
            except Exception:
                pass
        self.send_msg('\r\n已成功登出，刷新页面重新登录，关闭页面断开连接')
        self.chan.ssh.close()

        record_path = os.path.join(settings.MEDIA_ROOT, 'ssh_records', self.chan.scope['user'].username,
                                   time.strftime('%Y-%m-%d'))
        if not os.path.exists(record_path):
            os.makedirs(record_path, exist_ok=True)
        record_file_name = '{}.{}.cast'.format(self.chan.host_ip, time.strftime('%Y%m%d%H%M%S'))
        record_file_path = os.path.join(record_path, record_file_name)

        header = {
            "version": 2,
            "width": 120,
            "height": 35,
            "timestamp": round(start_time),
            "title": "Demo",
            "env": {
                "TERM": os.environ.get('TERM'),
                "SHELL": os.environ.get('SHELL', '/bin/bash')
            },
        }

        f = open(record_file_path, 'a')
        f.write(json.dumps(header) + '\n')
        for out in stdout:
            f.write(json.dumps(out) + '\n')
        f.close()
        login_status_time = time.time() - start_time
        if login_status_time >= 60:
            login_status_time = '{} m'.format(round(login_status_time / 60, 2))
        elif login_status_time >= 3600:
            login_status_time = '{} h'.format(round(login_status_time / 3660, 2))
        else:
            login_status_time = '{} s'.format(round(login_status_time))

        ssh_record.delay(ssh_login_user=self.chan.scope['user'], ssh_server=self.chan.host_ip,
                         ssh_remote_ip=self.chan.scope["client"][0], ssh_start_time=current_time,
                         ssh_login_status_time=login_status_time, ssh_record_file=record_file_path.split('media/')[1])

    def send_msg(self, msg):
        async_to_sync(self.chan.channel_layer.group_send)(
            self.chan.channel_name,
            {
                "type": "user.message",
                "text": msg
            },
        )


class SSHConsumer(WebsocketConsumer):
    def connect(self):
        path = self.scope['path']
        server_id = path.split('/')[3]
        host = ServerAssets.objects.select_related('assets').get(id=server_id)
        username = host.username
        self.host_ip = host.assets.asset_management_ip
        host_port = int(host.port)
        password = CryptPwd().decrypt_pwd(host.password)

        # 创建channels group， 命名为：用户名，并使用channel_layer写入到redis
        async_to_sync(self.channel_layer.group_add)(self.channel_name, self.channel_name)
        self.ssh = paramiko.SSHClient()
        self.ssh.load_system_host_keys()
        self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.ssh.connect(self.host_ip, host_port, username, password)
        self.chan = self.ssh.invoke_shell(term='xterm')
        self.chan.settimeout(0)
        t1 = MyThread(self)
        t1.setDaemon(True)
        t1.start()
        # 返回给receive方法处理
        self.accept()

    def receive(self, text_data=None, bytes_data=None):
        self.chan.send(text_data)

    def user_message(self, event):
        self.send(text_data=event["text"])

    def disconnect(self, close_code):
        async_to_sync(self.channel_layer.group_discard)(self.channel_name, self.channel_name)

