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
from assets.models import ServerAssets
from task.tasks import module_record
from users.models import UserProfile
from utils.db.redis_ops import RedisOps
from task.utils.ansible_api_v2 import ANSRunner
from task.utils.gen_resource import GenResource
from channels.generic.websocket import WebsocketConsumer


class AnsModuleConsumer(WebsocketConsumer):

    def __init__(self, *args, **kwargs):
        super(AnsModuleConsumer, self).__init__(*args, **kwargs)
        self.redis_instance = RedisOps(settings.REDIS_HOST, settings.REDIS_PORT, 4)
        self.ans_info = None

    def connect(self):
        self.accept()

    def receive(self, text_data=None, bytes_data=None):
        self.ans_info = json.loads(text_data)

        group_ids = self.ans_info['hostGroup']
        host_ids = self.ans_info['ans_group_hosts']
        selected_module_name = self.ans_info['ansibleModule']
        custom_model_name = self.ans_info.get('customModule', None)
        module_args = self.ans_info['ansibleModuleArgs']

        self.run_model(group_ids, host_ids, selected_module_name, custom_model_name, module_args)

    def disconnect(self, code):
        pass

    def run_model(self, group_ids, host_ids, selected_module_name, custom_model_name, module_args):
        gen_resource = GenResource()

        group_names = None
        if group_ids == ['custom'] or group_ids == ['all']:
            resource = gen_resource.gen_host_list(host_ids)
        else:
            resource, group_names = gen_resource.gen_group_dict(group_ids)

        host_list = [ServerAssets.objects.get(id=host_id).assets.asset_management_ip for host_id in host_ids]

        module_name = selected_module_name if selected_module_name != 'custom' else custom_model_name

        unique_key = '{}.{}.{}'.format(host_ids, module_name, module_args)

        if self.redis_instance.get(unique_key):
            self.send('<code style="color: #FF0000">\n有相同的任务正在进行！请稍后重试！\n</code>', close=True)
        else:
            try:
                self.redis_instance.set(unique_key, 1)
                ans = ANSRunner(resource, become='yes', become_method='sudo', become_user='root', sock=self)
                ans.run_module(host_list=host_list, module_name=module_name, module_args=module_args)
                ans_server = group_names if group_names else host_list

                module_record.delay(ans_user=UserProfile.objects.get(id=self.ans_info['run_user']),
                                    ans_remote_ip=self.ans_info['remote_ip'],
                                    ans_module=module_name,
                                    ans_args=module_args,
                                    ans_server=ans_server, ans_result=ans.get_module_results)
            except Exception as e:
                self.send('<code style="color: #FF0000">\nansible执行模块出错：{}\n</code>'.format(str(e)))
            finally:
                self.redis_instance.delete(unique_key)
                self.close()
