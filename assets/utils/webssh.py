# -*- coding: utf-8 -*-
import paramiko
import threading
import time
import os
import logging
from socket import timeout
from assets.tasks import admin_file
from channels.generic.websocket import WebsocketConsumer
from assets.models import ServerAssets, AdminRecord
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
                    break
            self.chan.send('\n由于长时间没有操作，连接已断开!')
            self.stdout.append([time.time() - self.start_time, 'o', '\n由于长时间没有操作，连接已断开!'])
            self.chan.close()

    def record(self):
        record_path = os.path.join(settings.MEDIA_ROOT, 'admin_ssh_records', self.chan.scope['user'].username,
                                   time.strftime('%Y-%m-%d'))
        if not os.path.exists(record_path):
            os.makedirs(record_path, exist_ok=True)
        record_file_name = '{}.{}.cast'.format(self.chan.host_ip, time.strftime('%Y%m%d%H%M%S'))
        record_file_path = os.path.join(record_path, record_file_name)

        header = {
            "version": 2,
            "width": self.chan.width,
            "height": self.chan.height,
            "timestamp": round(self.start_time),
            "title": "Demo",
            "env": {
                "TERM": os.environ.get('TERM'),
                "SHELL": os.environ.get('SHELL', '/bin/bash')
            },
        }

        admin_file.delay(record_file_path, self.stdout, header)

        login_status_time = time.time() - self.start_time
        if login_status_time >= 60:
            login_status_time = '{} m'.format(round(login_status_time / 60, 2))
        elif login_status_time >= 3600:
            login_status_time = '{} h'.format(round(login_status_time / 3660, 2))
        else:
            login_status_time = '{} s'.format(round(login_status_time))

        try:
            AdminRecord.objects.create(
                admin_login_user=self.chan.scope['user'],
                admin_server=self.chan.host_ip,
                admin_remote_ip=self.chan.remote_ip,
                admin_start_time=self.current_time,
                admin_login_status_time=login_status_time,
                admin_record_file=record_file_path.split('media/')[1]
            )
        except Exception as e:
            logging.getLogger().error('数据库添加用户操作记录失败，原因：{}'.format(e))


class SSHConsumer(WebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super(SSHConsumer, self).__init__(*args, **kwargs)
        self.ssh = paramiko.SSHClient()
        self.group_name = self.scope['url_route']['kwargs']['group_name']
        self.server = ServerAssets.objects.select_related('assets').get(id=self.scope['path'].split('/')[3])
        self.host_ip = self.server.assets.asset_management_ip
        self.width = 150
        self.height = 30
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
                             CryptPwd().decrypt_pwd(self.server.password), timeout=5)
        except Exception as e:
            logging.getLogger().error('用户{}通过webssh连接{}失败！原因：{}'.format(username, self.host_ip, e))
            self.send('用户{}通过webssh连接{}失败！原因：{}'.format(username, self.host_ip, e))
        self.chan = self.ssh.invoke_shell(term='xterm', width=self.width, height=self.height)
        # 设置如果3分钟没有任何输入，就断开连接
        self.chan.settimeout(60 * 3)
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
