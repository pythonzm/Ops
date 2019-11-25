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
import json
from ansible import constants as C
from collections import namedtuple
from ansible.parsing.dataloader import DataLoader
from ansible.playbook.play import Play
from ansible.executor.task_queue_manager import TaskQueueManager
from ansible.executor.playbook_executor import PlaybookExecutor
from ansible.plugins.callback import CallbackBase
from ansible.inventory.manager import InventoryManager
from ansible.vars.manager import VariableManager
from projs.utils.deploy_websocket import DeployResultsCollector
from conf.logger import ansible_logger
from django.conf import settings


class ModuleResultsCollector(CallbackBase):
    """
    直接执行模块命令的回调类
    """

    def __init__(self, sock=None, *args, **kwargs):
        super(ModuleResultsCollector, self).__init__(*args, **kwargs)
        self.module_results = []
        self.sock = sock

    def v2_runner_on_unreachable(self, result):
        if 'msg' in result._result:
            data = '<code style="color: #FF0000">\n{host} | unreachable | rc={rc} >> \n{stdout}\n</code>'.format(
                host=result._host.name, rc=result._result.get('rc'),
                stdout=result._result.get('msg').encode().decode('utf-8'))
        else:
            data = '<code style="color: #FF0000">\n{host} | unreachable >> \n{stdout}\n</code>'.format(
                host=result._host.name,
                stdout=json.dumps(result._result, indent=4, ensure_ascii=False))
        if self.sock:
            self.sock.send(data)
        self.module_results.append(data)

    def v2_runner_on_ok(self, result, *args, **kwargs):
        if 'rc' in result._result and 'stdout' in result._result:
            data = '<code style="color: #008000">\n{host} | success | rc={rc} >> \n{stdout}\n</code>'.format(
                host=result._host.name, rc=result._result.get('rc'),
                stdout=result._result.get('stdout').encode().decode('utf-8'))
        elif 'results' in result._result and 'rc' in result._result:
            data = '<code style="color: #008000">\n{host} | success | rc={rc} >> \n{stdout}\n</code>'.format(
                host=result._host.name, rc=result._result.get('rc'),
                stdout=result._result.get('results')[0].encode().decode('utf-8'))
        elif 'module_stdout' in result._result and 'rc' in result._result:
            data = '<code style="color: #008000">\n{host} | success | rc={rc} >> \n{stdout}\n</code>'.format(
                host=result._host.name, rc=result._result.get('rc'),
                stdout=result._result.get('module_stdout').encode().decode('utf-8'))
        else:
            data = '<code style="color: #008000">\n{host} | success >> \n{stdout}\n</code>'.format(
                host=result._host.name,
                stdout=json.dumps(result._result, indent=4, ensure_ascii=False))
        if self.sock:
            self.sock.send(data)
        self.module_results.append(data)

    def v2_runner_on_failed(self, result, *args, **kwargs):
        if 'stderr' in result._result:
            data = '<code style="color: #FF0000">\n{host} | failed | rc={rc} >> \n{stdout}\n</code>'.format(
                host=result._host.name,
                rc=result._result.get('rc'),
                stdout=result._result.get('stderr').encode().decode('utf-8'))
        elif 'module_stdout' in result._result:
            data = '<code style="color: #FF0000">\n{host} | failed | rc={rc} >> \n{stdout}\n</code>'.format(
                host=result._host.name,
                rc=result._result.get('rc'),
                stdout=result._result.get('module_stdout').encode().decode('utf-8'))
        else:
            data = '<code style="color: #FF0000">\n{host} | failed >> \n{stdout}\n</code>'.format(
                host=result._host.name,
                stdout=json.dumps(result._result, indent=4, ensure_ascii=False))
        if self.sock:
            self.sock.send(data)
        self.module_results.append(data)


class PlayBookResultsCollector(CallbackBase):
    """
    执行playbook的回调类
    """

    def __init__(self, sock, *args, **kwargs):
        super(PlayBookResultsCollector, self).__init__(*args, **kwargs)
        self.playbook_results = []
        self.sock = sock

    def v2_playbook_on_play_start(self, play):
        name = play.get_name().strip()
        if not name:
            msg = format('<code style="color: #FFFFFF">\nPLAY', '*<150') + ' \n</code>'
        else:
            msg = format(f'<code style="color: #FFFFFF">\nPLAY [{name}]', '*<150') + ' \n</code>'
        self.send_save(msg)

    def v2_playbook_on_task_start(self, task, is_conditional):
        msg = format(f'<code style="color: #FFFFFF">\nTASK [{task.get_name()}]', '*<150') + ' \n</code>'
        self.send_save(msg)

    def v2_runner_on_ok(self, result, *args, **kwargs):
        if result.is_changed():
            data = '<code style="color: #FFFF00">[{}]=> changed\n</code>'.format(result._host.name)
        else:
            data = '<code style="color: #008000">[{}]=> ok\n</code>'.format(result._host.name)
        self.send_save(data)

    def v2_runner_on_failed(self, result, *args, **kwargs):
        if 'changed' in result._result:
            del result._result['changed']
        data = '<code style="color: #FF0000">[{}]=> {}: {}\n</code>'.format(result._host.name, 'failed',
                                                                            self._dump_results(result._result))
        self.send_save(data)

    def v2_runner_on_unreachable(self, result):
        if 'changed' in result._result:
            del result._result['changed']
        data = '<code style="color: #FF0000">[{}]=> {}: {}\n</code>'.format(result._host.name, 'unreachable',
                                                                            self._dump_results(result._result))
        self.send_save(data)

    def v2_runner_on_skipped(self, result):
        if 'changed' in result._result:
            del result._result['changed']
        data = '<code style="color: #FFFF00">[{}]=> {}: {}\n</code>'.format(result._host.name, 'skipped',
                                                                            self._dump_results(result._result))
        self.send_save(data)

    def v2_playbook_on_stats(self, stats):
        hosts = sorted(stats.processed.keys())
        data = format('<code style="color: #FFFFFF">\nPLAY RECAP ', '*<150') + '\n'
        self.send_save(data)
        for h in hosts:
            s = stats.summarize(h)
            msg = '<code style="color: #FFFFFF">{} : ok={} changed={} unreachable={} failed={} skipped={}\n</code>'.format(
                h, s['ok'], s['changed'], s['unreachable'], s['failures'], s['skipped'])
            self.send_save(msg)

    def send_save(self, data):
        self.sock.send(data)
        self.playbook_results.append(data)


class MyInventory(InventoryManager):
    """
    用于动态生成Inventory的类.
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

            # 生成ansible主机变量
            self.get_host(ip).set_variable('ansible_ssh_host', ip)
            self.get_host(ip).set_variable('ansible_ssh_port', port)
            self.get_host(ip).set_variable('ansible_ssh_user', username)
            self.get_host(ip).set_variable('ansible_ssh_pass', password)
            self.get_host(ip).set_variable('ansible_sudo_pass', password)

            # 如果使用同一个密钥管理所有机器，只需把下方的注释去掉，ssh_key指定密钥文件，若是不同主机使用不同密钥管理，则需要单独设置主机变量或组变量
            # self.get_host(ip).set_variable('ansible_ssh_private_key_file', ssh_key)

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
    执行ansible模块或者playbook的类，这里默认采用了用户名+密码+sudo的方式
    """

    def __init__(self, resource=None, sources=None, sock=None, **kwargs):
        Options = namedtuple('Options', ['connection', 'module_path', 'forks', 'timeout', 'remote_user',
                                         'ask_pass', 'private_key_file', 'ssh_common_args', 'ssh_extra_args',
                                         'sftp_extra_args', 'strategy',
                                         'scp_extra_args', 'become', 'become_method', 'become_user', 'ask_value_pass',
                                         'verbosity', 'retry_files_enabled',
                                         'check', 'listhosts', 'listtasks', 'listtags', 'syntax', 'diff',
                                         'gathering', 'roles_path'])
        self.options = Options(connection='smart',
                               module_path=None,
                               forks=50, timeout=10,
                               remote_user=kwargs.get('remote_user', None), ask_pass=False, private_key_file=None,
                               ssh_common_args=None,
                               ssh_extra_args=None,
                               sftp_extra_args=None, strategy='free', scp_extra_args=None,
                               become=kwargs.get('become', None),
                               become_method=kwargs.get('become_method', None),
                               become_user=kwargs.get('become_user', None), ask_value_pass=False, verbosity=None,
                               retry_files_enabled=False, check=False, listhosts=False,
                               listtasks=False, listtags=False, syntax=False, diff=True, gathering='smart',
                               roles_path=settings.ANSIBLE_ROLE_PATH)
        self.loader = DataLoader()
        self.inventory = MyInventory(resource=resource, loader=self.loader, sources=sources)
        self.variable_manager = VariableManager(loader=self.loader, inventory=self.inventory)
        self.passwords = dict(sshpass=None, becomepass=None)
        self.callback = None
        self.sock = sock

    def run_module(self, host_list, module_name, module_args, deploy=False, send_msg=True):
        """
        run module from ansible ad-hoc.
        """
        self.callback = DeployResultsCollector(self.sock, send_msg=send_msg) if deploy else ModuleResultsCollector(
            sock=self.sock)

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

            C.HOST_KEY_CHECKING = False  # 关闭第一次使用ansible连接客户端是输入命令
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
            self.callback = PlayBookResultsCollector(sock=self.sock)
            if extra_vars:
                self.variable_manager.extra_vars = extra_vars
            executor = PlaybookExecutor(
                playbooks=[playbook_path], inventory=self.inventory, variable_manager=self.variable_manager,
                loader=self.loader,
                options=self.options, passwords=self.passwords,
            )
            executor._tqm._stdout_callback = self.callback
            C.HOST_KEY_CHECKING = False  # 关闭第一次使用ansible连接客户端是输入命令
            executor.run()
        except Exception as e:
            ansible_logger.error('执行{}失败，原因: {}'.format(playbook_path, e))

    @property
    def get_module_results(self):
        return self.callback.module_results

    @property
    def get_playbook_results(self):
        return self.callback.playbook_results
