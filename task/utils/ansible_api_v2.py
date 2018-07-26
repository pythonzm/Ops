# -*- coding: utf-8 -*-
"""
-------------------------------------------------
   File Name：      ansible_api
   Description:
   Author:          Administrator
   date：           2018/6/11
-------------------------------------------------
   Change Activity:
                    2018/6/11:
-------------------------------------------------
"""
import os
import json
from ansible import constants
from collections import namedtuple
from ansible.parsing.dataloader import DataLoader
from ansible.playbook.play import Play
from ansible.executor.task_queue_manager import TaskQueueManager
from ansible.executor.playbook_executor import PlaybookExecutor
from ansible.plugins.callback import CallbackBase
from ansible.inventory.manager import InventoryManager
from ansible.vars.manager import VariableManager
from conf.logger import ansible_logger


class ModelResultsCollector(CallbackBase):
    """
    直接执行模块命令的回调类
    """

    def __init__(self, *args, **kwargs):
        super(ModelResultsCollector, self).__init__(*args, **kwargs)
        self.host_ok = {}
        self.host_unreachable = {}
        self.host_failed = {}

    def v2_runner_on_unreachable(self, result):
        self.host_unreachable[result._host.get_name()] = result

    def v2_runner_on_ok(self, result, *args, **kwargs):
        self.host_ok[result._host.get_name()] = result

    def v2_runner_on_failed(self, result, *args, **kwargs):
        self.host_failed[result._host.get_name()] = result


class PlayBookResultsCollector(CallbackBase):
    """
    执行playbook的回调类
    """

    def __init__(self, *args, **kwargs):
        super(PlayBookResultsCollector, self).__init__(*args, **kwargs)
        self.task_ok = {}
        self.task_skipped = {}
        self.task_failed = {}
        self.task_status = {}
        self.task_unreachable = {}

    def v2_runner_on_ok(self, result, *args, **kwargs):
        self.task_ok[result._host.get_name()] = result

    def v2_runner_on_failed(self, result, *args, **kwargs):
        self.task_failed[result._host.get_name()] = result

    def v2_runner_on_unreachable(self, result):
        self.task_unreachable[result._host.get_name()] = result

    def v2_runner_on_skipped(self, result):
        self.task_ok[result._host.get_name()] = result

    def v2_playbook_on_stats(self, stats):
        hosts = sorted(stats.processed.keys())
        for h in hosts:
            t = stats.summarize(h)
            self.task_status[h] = {
                "ok": t['ok'],
                "changed": t['changed'],
                "unreachable": t['unreachable'],
                "skipped": t['skipped'],
                "failed": t['failures']
            }


class MyInventory(InventoryManager):
    """
    this is my ansible inventory object.
    """

    def __init__(self, loader, resource=None, sources=None):
        """
        resource的数据格式是一个列表字典，比如
            {
                "group1": {
                    "hosts": [{"ip": "10.0.0.0", "port": "22", "username": "test", "password": "pass"}, ...],
                    "group_vars": {"var1": value1, "var2": value2, ...}
                }
            }
             如果你只传入1个列表，这默认该列表内的所有主机属于default 组,比如
            [{"ip": "10.0.0.0", "port": "22", "username": "test", "password": "pass"}, ...]

        sources是原生的方法，参数是配置的inventory文件路径，可以指定一个，也可以以列表的形式可以指定多个
        """
        super(MyInventory, self).__init__(loader=loader, sources=sources)
        self.resource = resource
        self.dynamic_inventory()

    def add_dynamic_group(self, hosts, group_name, group_vars=None):
        """
        将从数据库读取的组信息，主机信息等生成的resource信息解析成ansible可以读取的内容
        :param hosts: 包含主机所有信息的的列表
        :type hosts: list
        :param group_name:
        :param group_vars:
        :type group_vars: dict
        :return:
        """
        # 添加主机组
        self.add_group(group_name)

        # 添加主机组变量
        if group_vars:
            for key, value in group_vars.items():
                self.groups[group_name].set_variable(key, value)

        for host in hosts:
            ip = host.get('ip')
            port = host.get('port')

            # 添加主机到主机组
            self.add_host(ip, group_name, port)

            username = host.get('username')
            password = host.get('password')
            if username == 'root':
                ssh_key = '/root/.ssh/id_rsa'
            else:
                ssh_key = '/home/{}/.ssh/id_rsa'.format(username)
            if not os.path.exists(ssh_key):
                ssh_key = host.get('ssh_key')

            # 生成ansible主机变量
            self.get_host(ip).set_variable('ansible_ssh_host', ip)
            self.get_host(ip).set_variable('ansible_ssh_port', port)
            self.get_host(ip).set_variable('ansible_ssh_user', username)
            self.get_host(ip).set_variable('ansible_ssh_pass', password)
            self.get_host(ip).set_variable('ansible_sudo_pass', password)
            self.get_host(ip).set_variable('ansible_ssh_private_key_file', ssh_key)

            # set other variables
            for key, value in host.items():
                if key not in ["ip", "port", "username", "password"]:
                    self.get_host(ip).set_variable(key, value)

    def dynamic_inventory(self):
        if isinstance(self.resource, list):
            self.add_dynamic_group(self.resource, 'default')
        elif isinstance(self.resource, dict):
            for groupname, hosts_and_vars in self.resource.items():
                self.add_dynamic_group(hosts_and_vars.get("hosts"), groupname, hosts_and_vars.get("group_vars"))


class ANSRunner(object):
    """
    执行ansible模块或者playbook的类
    """

    def __init__(self, resource=None, sources=None):
        Options = namedtuple('Options', ['connection', 'module_path', 'forks', 'timeout', 'remote_user',
                                         'ask_pass', 'private_key_file', 'ssh_common_args', 'ssh_extra_args',
                                         'sftp_extra_args', 'strategy',
                                         'scp_extra_args', 'become', 'become_method', 'become_user', 'ask_value_pass',
                                         'verbosity',
                                         'check', 'listhosts', 'listtasks', 'listtags', 'syntax', 'diff'])
        self.options = Options(connection='smart', module_path=None, forks=100, timeout=10,
                               remote_user=None, ask_pass=False, private_key_file=None,
                               ssh_common_args=None,
                               ssh_extra_args=None,
                               sftp_extra_args=None, strategy='free', scp_extra_args=None, become=None,
                               become_method=None,
                               become_user=None, ask_value_pass=False, verbosity=None, check=False, listhosts=False,
                               listtasks=False, listtags=False, syntax=False, diff=True)
        self.loader = DataLoader()
        self.inventory = MyInventory(resource=resource, loader=self.loader, sources=sources)
        self.variable_manager = VariableManager(loader=self.loader, inventory=self.inventory)
        self.passwords = dict(sshpass=None, becomepass=None)
        self.callback = None

    def run_module(self, host_list, module_name, module_args):
        """
        run module from ansible ad-hoc.
        """
        self.callback = ModelResultsCollector()
        play_source = dict(
            name="Ansible Play",
            hosts=host_list,
            gather_facts='no',
            tasks=[dict(action=dict(module=module_name, args=module_args))]
        )

        play = Play().load(play_source, variable_manager=self.variable_manager, loader=self.loader)

        # actually run it
        tqm = None

        try:
            tqm = TaskQueueManager(
                inventory=self.inventory,
                variable_manager=self.variable_manager,
                loader=self.loader,
                options=self.options,
                passwords=self.passwords,
                stdout_callback=self.callback,
            )

            constants.HOST_KEY_CHECKING = False  # 关闭第一次使用ansible连接客户端是输入命令
            tqm.run(play)
        except Exception as e:
            ansible_logger.error('执行{}失败，原因: {}'.format(module_name, e))
        finally:
            if tqm is not None:
                tqm.cleanup()

    def run_playbook(self, playbook_path, extra_vars=None):
        """
        run ansible playbook
        """
        try:
            self.callback = PlayBookResultsCollector()
            if extra_vars:
                self.variable_manager.extra_vars = extra_vars
            executor = PlaybookExecutor(
                playbooks=[playbook_path], inventory=self.inventory, variable_manager=self.variable_manager,
                loader=self.loader,
                options=self.options, passwords=self.passwords,
            )
            executor._tqm._stdout_callback = self.callback
            constants.HOST_KEY_CHECKING = False  # 关闭第一次使用ansible连接客户端是输入命令
            executor.run()
        except Exception as e:
            ansible_logger.error('执行{}失败，原因: {}'.format(playbook_path, e))

    def get_model_result(self):
        results_raw = []
        for host, result in self.callback.host_ok.items():
            if 'rc' in result._result and 'stdout' in result._result:
                data = "{host} | success | rc={rc} >> \n{stdout}\n".format(host=host, rc=result._result.get('rc'),
                                                                           stdout=result._result.get('stdout'))
            elif 'results' in result._result and 'rc' in result._result:
                data = "{host} | success | rc={rc} >> \n{stdout}\n".format(host=host, rc=result._result.get('rc'),
                                                                           stdout=result._result.get('results')[0])
            else:
                data = "{host} | success >> \n{stdout}\n".format(host=host, stdout=json.dumps(result._result, indent=4))
            results_raw.append(data)

        for host, result in self.callback.host_failed.items():
            if 'msg' in result._result:
                data = "{host} | failed | rc={rc} >> \n{stdout}\n".format(host=host, rc=result._result.get('rc'),
                                                                          stdout=result._result.get('msg'))
            else:
                data = "{host} | failed >> \n{stdout}\n".format(host=host,
                                                                stdout=json.dumps(result._result, indent=4))
            results_raw.append(data)

        for host, result in self.callback.host_unreachable.items():
            if 'msg' in result._result:
                data = "{host} | unreachable | rc={rc} >> \n{stdout}\n".format(host=host, rc=result._result.get('rc'),
                                                                               stdout=result._result.get('msg'))
            else:
                data = "{host} | unreachable >> \n{stdout}\n".format(host=host,
                                                                     stdout=json.dumps(result._result, indent=4))
            results_raw.append(data)

        return results_raw

    def get_playbook_result(self):
        results_raw = {'skipped': {}, 'failed': {}, 'ok': {}, "status": {}, 'unreachable': {}, "changed": {}}
        for host, result in self.callback.task_ok.items():
            results_raw['ok'][host] = result

        for host, result in self.callback.task_failed.items():
            results_raw['failed'][host] = result

        for host, result in self.callback.task_status.items():
            results_raw['status'][host] = result

        for host, result in self.callback.task_skipped.items():
            results_raw['skipped'][host] = result

        for host, result in self.callback.task_unreachable.items():
            results_raw['unreachable'][host] = result

        return results_raw

    def get_group_dict(self):
        group_dict = self.inventory.get_groups_dict()
        return group_dict

    def get_group_names(self):
        group_names = self.inventory.list_groups()
        return group_names
