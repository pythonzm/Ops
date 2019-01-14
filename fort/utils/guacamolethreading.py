# -*- coding: utf-8 -*-
import threading
import json
from utils.db.redis_ops import RedisOps
from django.conf import settings


def get_redis_instance():
    redis_instance = RedisOps(settings.REDIS_HOST, settings.REDIS_PORT, 7)
    return redis_instance


import ast
import logging

logger = logging.getLogger(__name__)
import time


class GuacamoleThread(threading.Thread):
    """Thread class with a stop() method. The thread itself has to check
    regularly for the stopped() condition."""

    def __init__(self, message, client):
        super(GuacamoleThread, self).__init__()
        self._stop_event = threading.Event()
        self.message = message
        self.queue = self.redis_queue()
        self.client = client
        self.read_lock = threading.RLock()
        self.write_lock = threading.RLock()
        self.pending_read_request = threading.Event()

    def stop(self):
        self._stop_event.set()

    def stopped(self):
        return self._stop_event.is_set()

    def redis_queue(self):
        redis_instance = get_redis_instance()
        redis_sub = redis_instance.r.pubsub()
        redis_sub.subscribe(self.message.channel_name)
        return redis_sub

    def run(self):
        # while (not self._stop_event.is_set()):
        # text = self.queue.get_message()
        # if text:
        # if isinstance(data,(list,tuple)):
        # if data[0] == 'close':
        # self.stop()
        with self.read_lock:
            # self.pending_read_request.clear()

            while True:
                instruction = self.client.receive()
                print(instruction)
                if instruction:
                    self.message.send(json.dumps({
                        "type": "websocket.send",
                        "text": instruction,
                    }))
                else:
                    break

                # if self.pending_read_request.is_set():
                # logger.info('Letting another request take over.')
                # break

            # End-of-instruction marker
            self.message.send(json.dumps({
                "type": "websocket.send",
                "text": '0.;'
            }))


class GuacamoleThreadWrite(GuacamoleThread):

    def run(self):
        while True:
            text = self.queue.get_message()
            print(text)
            try:
                data = ast.literal_eval(text['data'])
            except Exception:
                if isinstance(text, dict) and 'data' in text:
                    data = text['data']
                elif isinstance(text, str):
                    data = text
                else:
                    data = text

            if data:
                if isinstance(data, (list, tuple)):
                    if data[0] == 'close':
                        self.stop()
                if isinstance(data, int) and data == 1:
                    pass
                else:
                    # print 'write',data
                    with self.write_lock:
                        self.client.send(str(data))
            else:
                time.sleep(0.001)
