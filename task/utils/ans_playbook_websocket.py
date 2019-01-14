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
from task.tasks import playbook_record
from task.models import AnsiblePlaybook
from users.models import UserProfile
from task.utils.ansible_api_v2 import ANSRunner
from task.utils.gen_resource import GenResource
from channels.generic.websocket import WebsocketConsumer
from task.utils.ansible_api_v2 import PlayBookResultsCollector


class PlaybookThread(threading.Thread):
    def __init__(self, ans):
        super(PlaybookThread, self).__init__()
        self.ans = ans
        self._stop_event = threading.Event()
        self.pub = ans.redis_instance.redis_conn.pubsub()
        self.playbook_results = []

    def stop(self):
        self.pub.unsubscribe(self.ans.channel_key)
        self._stop_event.set()

    def run(self):
        self.pub.subscribe(self.ans.channel_key)

        while not self._stop_event.is_set():
            time.sleep(0.1)
            text = self.pub.listen()
            for i in text:
                if i["type"] == "message":
                    self.ans.send(i['data'])
                    self.playbook_results.append(i['data'])

    @property
    def results(self):
        return self.playbook_results


class AnsPlaybookConsumer(WebsocketConsumer):

    def __init__(self, *args, **kwargs):
        super(AnsPlaybookConsumer, self).__init__(*args, **kwargs)
        self.playbook = PlayBookResultsCollector()
        self.redis_instance = self.playbook.redis_instance
        self.channel_key = self.playbook.channel_key
        self.playbook_thread = PlaybookThread(self)
        self.ans_info = None

    def connect(self):
        self.playbook_thread.setDaemon(True)
        self.playbook_thread.start()
        self.accept()

    def receive(self, text_data=None, bytes_data=None):
        self.ans_info = json.loads(text_data)

        group_ids = self.ans_info['group_ids']
        playbook_id = self.ans_info['playbook_id']

        self.run_playbook(group_ids, playbook_id)

    def disconnect(self, code):
        pass

    def run_playbook(self, group_ids, playbook_id):
        playbook = AnsiblePlaybook.objects.select_related('playbook_user').get(id=playbook_id)
        unique_key = '{}.{}'.format(playbook.playbook_name, group_ids)

        if self.redis_instance.get(unique_key):
            self.playbook_thread.stop()
            self.send('<code style="color: #FF0000">\n有相同的任务正在进行！请稍后重试！\n</code>')
            self.close()
        else:
            try:
                self.redis_instance.set(unique_key, 1)
                resource = GenResource().gen_group_dict(group_ids)

                ans = ANSRunner(resource)
                ans.run_playbook(playbook.playbook_file.path)

                playbook_record.delay(
                    playbook_user=UserProfile.objects.get(id=self.ans_info['run_user']),
                    playbook_remote_ip=self.ans_info['remote_ip'],
                    playbook_name=playbook.playbook_name,
                    playbook_result=self.playbook_thread.results
                )
            except Exception as e:
                self.send('<code style="color: #FF0000">\nansible执行playbook出错：{}\n</code>'.format(str(e)))
            finally:
                self.redis_instance.delete(unique_key)
                self.playbook_thread.stop()
                self.close()
