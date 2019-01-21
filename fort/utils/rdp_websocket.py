# -*- coding: utf-8 -*-
import time
import logging
import threading
from socket import timeout
from channels.generic.websocket import WebsocketConsumer
from guacamole.client import GuacamoleClient
from assets.models import ServerAssets
from fort.models import FortServerUser
from django.conf import settings
from utils.db.redis_ops import RedisOps


class GuacamoleThread(threading.Thread):
    """Thread class with a stop() method. The thread itself has to check
    regularly for the stopped() condition."""

    def __init__(self, message):
        super(GuacamoleThread, self).__init__()
        self._stop_event = threading.Event()
        self.message = message
        self.redis_instance = RedisOps(settings.REDIS_HOST, settings.REDIS_PORT, 9)
        self.read_lock = threading.RLock()
        self.write_lock = threading.RLock()

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
                except timeout:
                    logging.getLogger().error('连接超时！')
                    break

            # End-of-instruction marker
            self.message.send('0.;')


class GuacamoleConsumer(WebsocketConsumer):

    def __init__(self, *args, **kwargs):
        super(GuacamoleConsumer, self).__init__(*args, **kwargs)
        self.client = GuacamoleClient(settings.GUACD_HOST, settings.GUACD_PORT)
        self.group_name = self.scope['url_route']['kwargs']['group_name']
        self.fort_server = ServerAssets.objects.select_related('assets').get(id=self.scope['path'].split('/')[3])
        self.fort_user = FortServerUser.objects.get(id=self.scope['path'].split('/')[4])
        self.guacamole_thread = GuacamoleThread(self)

    def connect(self):
        self.accept('guacamole')

        server_protocol = self.fort_user.fort_server.server_protocol
        if server_protocol == 'vnc':
            self.client.handshake(protocol=server_protocol,
                                  hostname=self.fort_server.assets.asset_management_ip,
                                  port=self.fort_user.fort_vnc_port,
                                  password=self.fort_user.fort_password)
        elif server_protocol == 'rdp':
            self.client.handshake(protocol=server_protocol,
                                  hostname=self.fort_server.assets.asset_management_ip, port=self.fort_server.port,
                                  password=self.fort_user.fort_password,
                                  username=self.fort_user.fort_username)
        self.send('0.,{0}.{1};'.format(len(self.group_name), self.group_name))
        self.guacamole_thread.setDaemon(True)
        self.guacamole_thread.start()

    def disconnect(self, event):
        self.guacamole_thread.stop()

    def receive(self, text_data=None, bytes_data=None):
        with self.guacamole_thread.write_lock:
            self.client.send(text_data)
