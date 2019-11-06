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
from fort.tasks import fort_file
from assets.tasks import admin_file
from assets.models import AdminRecord
from fort.models import FortRecord
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
        record_path = os.path.join(settings.MEDIA_ROOT, self.message.record_dir, self.message.scope['user'].username,
                                   time.strftime('%Y-%m-%d'))
        if not os.path.exists(record_path):
            os.makedirs(record_path, exist_ok=True)
        record_file_name = '{}.{}.guac'.format(self.message.ip, time.strftime('%Y%m%d%H%M%S'))
        record_file_path = os.path.join(record_path, record_file_name)

        login_status_time = self.format_time(time.time() - self.start_time)
        login_user = self.message.scope['user']
        login_server = r'{}@{}'.format(self.message.username, self.message.ip)

        try:
            if login_user.is_superuser:
                admin_file.delay(record_file_path, self.txt)
                AdminRecord.objects.create(
                    admin_login_user=login_user,
                    admin_server=login_server,
                    admin_remote_ip=self.message.remote_ip,
                    admin_start_time=self.current_time,
                    admin_login_status_time=login_status_time,
                    admin_record_file=record_file_path.split('media/')[1],
                    admin_record_mode='guacamole'
                )
            else:
                fort_file.delay(record_file_path, self.txt)
                FortRecord.objects.create(
                    login_user=login_user,
                    fort=login_server,
                    remote_ip=self.message.remote_ip,
                    start_time=self.current_time,
                    login_status_time=login_status_time,
                    record_file=record_file_path.split('media/')[1],
                    record_mode='guacamole'
                )
        except Exception as e:
            logging.getLogger().error('数据库添加用户操作记录失败，原因：{}'.format(e))

    @staticmethod
    def format_time(seconds):
        m, s = divmod(seconds, 60)
        h, m = divmod(m, 60)
        if h:
            return "%02dh:%02dm:%02ds" % (h, m, s)
        if m:
            return "%02dm:%02ds" % (m, s)
        else:
            return "%02ds" % s


class MyGuacamole(WebsocketConsumer):

    def __init__(self, *args, **kwargs):
        super(MyGuacamole, self).__init__(*args, **kwargs)
        self.client = GuacamoleClient(settings.GUACD_HOST, settings.GUACD_PORT, timeout=5)
        self.group_name = self.scope['url_route']['kwargs']['group_name']
        self.guacamole_thread = GuacamoleThread(self)
        self.query_list = self.scope['query_string'].decode('utf8').split(',')
        self.remote_ip = self.query_list[0].strip()
        self.width = self.query_list[1].strip()
        self.height = self.query_list[2].strip()
        self.dpi = self.query_list[3].strip()
        self.ip = None
        self.port = None
        self.username = None
        self.password = None
        self.record_dir = 'admin_guacamole_records' if self.scope['user'].is_superuser else 'fort_guacamole_records'

    def connect(self):
        if self.scope["user"].is_anonymous:
            self.close(code=1007)
        else:
            self.accept('guacamole')

        self.client.handshake(protocol='rdp', hostname=self.ip, port=self.port, password=self.password,
                              username=self.username, width=self.width, height=self.height, dpi=self.dpi)
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
