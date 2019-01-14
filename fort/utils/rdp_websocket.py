# -*- coding: utf-8 -*-
from channels.generic.websocket import WebsocketConsumer
from fort.utils.guacamolethreading import get_redis_instance
from guacamole.client import GuacamoleClient
import uuid
from django.conf import settings
from fort.utils.guacamolethreading import GuacamoleThread, GuacamoleThreadWrite
import json


class GuacamoleConsumer(WebsocketConsumer):
    def websocket_connect(self, message):
        self.accept()

    def websocket_disconnect(self, event):
        # close threading
        self.send(json.dumps({
            "type": "websocket.send",
            "text": event["text"],
        }))

    def queue(self):
        queue = get_redis_instance()
        channel = queue.pubsub()
        return queue

    def closeguacamole(self):
        # close threading
        self.queue().publish(self.channel_name, json.dumps(['close']))

    def websocket_receive(self, text=None, bytes=None, **kwargs):
        client = GuacamoleClient(settings.GUACD_HOST, settings.GUACD_PORT)
        client.handshake(protocol='vnc', hostname='10.1.19.11', port=5901, password='123456')
        cache_key = str(uuid.uuid4())
        self.send(json.dumps({
            "type": "websocket.send",
            "text": '0.,{0}.{1};'.format(len(cache_key), cache_key),
        }))
        # '0.,36.83940151-b2f9-4743-b5e4-b6eb85a97743;'

        guacamolethread = GuacamoleThread(self, client)
        guacamolethread.setDaemon = True
        guacamolethread.start()

        guacamolethreadwrite = GuacamoleThreadWrite(self, client)
        guacamolethreadwrite.setDaemon = True
        guacamolethreadwrite.start()
        print(text)
        # print 'receive',text
        self.queue().publish(self.channel_name, text['text'])
