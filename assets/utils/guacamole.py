# -*- coding: utf-8 -*-
"""
-------------------------------------------------
   File Name：      root_rdp
   Description:
   Author:          Administrator
   date：           2019-01-21
-------------------------------------------------
   Change Activity:
                    2019-01-21:
-------------------------------------------------
"""
import os
import time
import logging
import threading
from socket import timeout
from django.conf import settings
from assets.tasks import admin_file
from utils.crypt_pwd import CryptPwd
from assets.models import ServerAssets, AdminRecord
from utils.db.redis_ops import RedisOps
from guacamole.client import GuacamoleClient
from channels.generic.websocket import WebsocketConsumer


class GuacamoleThread(threading.Thread):
    """Thread class with a stop() method. The thread itself has to check
    regularly for the stopped() condition."""

    def __init__(self, message):
        super(GuacamoleThread, self).__init__()
        self._stop_event = threading.Event()
        self.start_time = time.time()
        self.current_time = time.strftime(settings.TIME_FORMAT)
        self.message = message
        self.redis_instance = RedisOps(settings.REDIS_HOST, settings.REDIS_PORT, 9)
        self.read_lock = threading.RLock()
        self.write_lock = threading.RLock()
        self.txt = []

    def stop(self):
        self._stop_event.set()

    def run(self):
        with self.read_lock:
            while not self._stop_event.is_set():
                time.sleep(0.001)
                try:
                    instruction = self.message.client.receive()
                    if instruction:
                        self.message.send(instruction)
                        self.txt.append(instruction)
                except timeout:
                    logging.getLogger().error('连接超时！')
                    break
                except OSError:
                    break
            # End-of-instruction marker
            self.message.send('0.;')

    def record(self):
        record_path = os.path.join(settings.MEDIA_ROOT, 'admin_guacamole_records', self.message.scope['user'].username,
                                   time.strftime('%Y-%m-%d'))
        if not os.path.exists(record_path):
            os.makedirs(record_path, exist_ok=True)
        record_file_name = '{}.{}.guac'.format(self.message.server_ip, time.strftime('%Y%m%d%H%M%S'))
        record_file_path = os.path.join(record_path, record_file_name)

        admin_file.delay(record_file_path, self.txt)

        login_status_time = time.time() - self.start_time
        if login_status_time >= 60:
            login_status_time = '{} m'.format(round(login_status_time / 60, 2))
        elif login_status_time >= 3600:
            login_status_time = '{} h'.format(round(login_status_time / 3660, 2))
        else:
            login_status_time = '{} s'.format(round(login_status_time))

        try:
            AdminRecord.objects.create(
                admin_login_user=self.message.scope['user'],
                admin_server=self.message.server_ip,
                admin_remote_ip=self.message.remote_ip,
                admin_start_time=self.current_time,
                admin_login_status_time=login_status_time,
                admin_record_file=record_file_path.split('media/')[1],
                admin_record_mode='guacamole'
            )
        except Exception as e:
            logging.getLogger().error('数据库添加用户操作记录失败，原因：{}'.format(e))


class AdminGuacamole(WebsocketConsumer):

    def __init__(self, *args, **kwargs):
        super(AdminGuacamole, self).__init__(*args, **kwargs)
        self.client = GuacamoleClient(settings.GUACD_HOST, settings.GUACD_PORT, timeout=5)
        self.group_name = self.scope['url_route']['kwargs']['group_name']
        self.server = ServerAssets.objects.select_related('assets').get(id=self.scope['path'].split('/')[3])
        self.guacamole_thread = GuacamoleThread(self)
        self.query_list = self.scope['query_string'].decode('utf8').split(',')
        self.remote_ip = self.query_list[0].strip()
        self.width = self.query_list[1].strip()
        self.height = self.query_list[2].strip()
        self.dpi = self.query_list[3].strip()
        self.server_ip = self.server.assets.asset_management_ip

    def connect(self):
        self.accept('guacamole')

        self.client.handshake(protocol='rdp',
                              hostname=self.server_ip, port=self.server.port,
                              password=CryptPwd().decrypt_pwd(self.server.password),
                              username=self.server.username, width=self.width, height=self.height, dpi=self.dpi)
        self.send('0.,{0}.{1};'.format(len(self.group_name), self.group_name))
        self.guacamole_thread.setDaemon(True)
        self.guacamole_thread.start()

    def disconnect(self, event):
        try:
            self.guacamole_thread.record()
        finally:
            self.guacamole_thread.stop()
            self.client.close()

    def receive(self, text_data=None, bytes_data=None):
        with self.guacamole_thread.write_lock:
            self.client.send(text_data)
