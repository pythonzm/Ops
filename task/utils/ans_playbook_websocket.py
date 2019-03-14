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
from django.conf import settings
from task.tasks import playbook_record
from task.models import AnsiblePlaybook
from users.models import UserProfile
from utils.db.redis_ops import RedisOps
from task.utils.ansible_api_v2 import ANSRunner
from task.utils.gen_resource import GenResource
from channels.generic.websocket import WebsocketConsumer


class AnsPlaybookConsumer(WebsocketConsumer):

    def __init__(self, *args, **kwargs):
        super(AnsPlaybookConsumer, self).__init__(*args, **kwargs)
        self.redis_instance = RedisOps(settings.REDIS_HOST, settings.REDIS_PORT, 4)
        self.ans_info = None

    def connect(self):
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
            self.send('<code style="color: #FF0000">\n有相同的任务正在进行！请稍后重试！\n</code>', close=True)
        else:
            try:
                self.redis_instance.set(unique_key, 1)
                resource = GenResource().gen_group_dict(group_ids)

                ans = ANSRunner(resource, sock=self)
                ans.run_playbook(playbook.playbook_file.path)

                playbook_record.delay(
                    playbook_user=UserProfile.objects.get(id=self.ans_info['run_user']),
                    playbook_remote_ip=self.ans_info['remote_ip'],
                    playbook_name=playbook.playbook_name,
                    playbook_result=ans.get_playbook_results
                )
            except Exception as e:
                self.send('<code style="color: #FF0000">\nansible执行playbook出错：{}\n</code>'.format(str(e)))
            finally:
                self.redis_instance.delete(unique_key)
                self.close()
