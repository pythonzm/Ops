# -*- coding: utf-8 -*-
import paramiko
import threading
import time
import os
import json
import logging
from socket import timeout
from channels.generic.websocket import WebsocketConsumer
from assets.models import ServerAssets, SSHRecord
from Ops import settings
from utils.crypt_pwd import CryptPwd


class MyThread(threading.Thread):
    def __init__(self, chan):
        super(MyThread, self).__init__()
        self.chan = chan
        self._stop_event = threading.Event()
        self.start_time = time.time()
        self.current_time = time.strftime(settings.TIME_FORMAT)
        self.stdout = []
        self.read_lock = threading.RLock()

    def stop(self):
        self._stop_event.set()

    def run(self):
        with self.read_lock:
            while not self._stop_event.is_set():
                time.sleep(0.1)
                try:
                    data = self.chan.chan.recv(1024)
                    if data:
                        str_data = bytes.decode(data)
                        self.chan.send(str_data)
                        self.stdout.append([time.time() - self.start_time, 'o', str_data])
                except timeout:
                    pass

    def record(self):
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
            "timestamp": round(self.start_time),
            "title": "Demo",
            "env": {
                "TERM": os.environ.get('TERM'),
                "SHELL": os.environ.get('SHELL', '/bin/bash')
            },
        }

        f = open(record_file_path, 'a')
        f.write(json.dumps(header) + '\n')
        for out in self.stdout:
            f.write(json.dumps(out) + '\n')
        f.close()
        login_status_time = time.time() - self.start_time
        if login_status_time >= 60:
            login_status_time = '{} m'.format(round(login_status_time / 60, 2))
        elif login_status_time >= 3600:
            login_status_time = '{} h'.format(round(login_status_time / 3660, 2))
        else:
            login_status_time = '{} s'.format(round(login_status_time))

        SSHRecord.objects.create(
            ssh_login_user=self.chan.scope['user'],
            ssh_server=self.chan.host_ip,
            ssh_remote_ip=self.chan.remote_ip,
            ssh_start_time=self.current_time,
            ssh_login_status_time=login_status_time,
            ssh_record_file=record_file_path.split('media/')[1]
        )


class SSHConsumer(WebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super(SSHConsumer, self).__init__(*args, **kwargs)
        self.ssh = paramiko.SSHClient()
        self.group_name = self.scope['url_route']['kwargs']['group_name']
        self.server = ServerAssets.objects.select_related('assets').get(id=self.scope['path'].split('/')[3])
        self.host_ip = self.server.assets.asset_management_ip
        self.t1 = MyThread(self)
        self.chan = None
        self.remote_ip = None

    def connect(self):
        self.accept()

        username = self.server.username
        try:
            self.ssh.load_system_host_keys()
            self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            self.ssh.connect(self.host_ip, int(self.server.port), username,
                             CryptPwd().decrypt_pwd(self.server.password))
        except Exception as e:
            logging.getLogger().error('用户{}通过webssh连接{}失败！原因：{}'.format(username, self.host_ip, e))
            self.send('用户{}通过webssh连接{}失败！原因：{}'.format(username, self.host_ip, e))
        self.chan = self.ssh.invoke_shell(term='xterm', width=150, height=30)
        self.chan.settimeout(0)
        self.t1.setDaemon(True)
        self.t1.start()

    def receive(self, text_data=None, bytes_data=None):
        if text_data[0].isdigit():
            self.remote_ip = text_data
        else:
            self.chan.send(text_data)

    def disconnect(self, close_code):
        try:
            self.t1.record()
        finally:
            self.ssh.close()
            self.t1.stop()
