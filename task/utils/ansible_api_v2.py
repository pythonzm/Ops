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
import re
from ansible import constants as C
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
        self.task_skipped = []
        self.task_failed = []
        self.task_status = {}
        self.task_unreachable = []
        self.task_ok = []

    def v2_runner_on_ok(self, result, *args, **kwargs):
        self.task_ok.append({result._host.name: result})

    def v2_runner_on_failed(self, result, *args, **kwargs):
        self.task_failed.append({result._host.name: result})

    def v2_runner_on_unreachable(self, result):
        self.task_unreachable.append({result._host.name: result})

    def v2_runner_on_skipped(self, result):
        self.task_skipped.append({result._host.name: result})

    def v2_playbook_on_stats(self, stats):
        hosts = sorted(stats.processed.keys())
        for h in hosts:
            s = stats.summarize(h)
            self.task_status[h] = s


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

    def __init__(self, resource=None, sources=None, **kwargs):
        Options = namedtuple('Options', ['connection', 'module_path', 'forks', 'timeout', 'remote_user',
                                         'ask_pass', 'private_key_file', 'ssh_common_args', 'ssh_extra_args',
                                         'sftp_extra_args', 'strategy',
                                         'scp_extra_args', 'become', 'become_method', 'become_user', 'ask_value_pass',
                                         'verbosity',
                                         'check', 'listhosts', 'listtasks', 'listtags', 'syntax', 'diff',
                                         'gathering'])
        self.options = Options(connection='smart',
                               module_path=None,
                               forks=50, timeout=10,
                               remote_user=None, ask_pass=False, private_key_file=None,
                               ssh_common_args=None,
                               ssh_extra_args=None,
                               sftp_extra_args=None, strategy='free', scp_extra_args=None, become=kwargs.get('become', None),
                               become_method=kwargs.get('become_method', None),
                               become_user=kwargs.get('become_user', None), ask_value_pass=False, verbosity=None, check=False, listhosts=False,
                               listtasks=False, listtags=False, syntax=False, diff=True, gathering='smart')
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
            self.callback = PlayBookResultsCollector()
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
            if 'stderr' in result._result:
                data = "{host} | failed | rc={rc} >> \n{stdout}\n".format(host=host, rc=result._result.get('rc'),
                                                                          stdout=result._result.get(
                                                                              'stderr').encode().decode('utf-8'))
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
        results_raw = []
        for task_obj in self.callback.task_ok:
            for host, result in task_obj.items():
                for remove_key in (
                        'invocation', '_ansible_parsed', '_ansible_no_log', '_ansible_verbose_always', 'failed',
                        'stdout', 'diff', 'results', 'status', 'warnings', 'stdout_lines'):
                    if remove_key in result._result:
                        del result._result[remove_key]
                if result._result.get('changed'):
                    data = '<code style="color: #FFFF00">TASK [{}] {}\n{}: changed\n{}\n</code><br>'.format(
                        result.task_name, '*' * 100, host, result._result)
                else:
                    data = '<code style="color: #008000">TASK [{}] {}\n{}: success\n{}\n</code><br>'.format(
                        result.task_name, '*' * 100, host, result._result)
                results_raw.append(data)

        for task_obj in self.callback.task_failed:
            for host, result in task_obj.items():
                data = '<code style="color: #FF0000">TASK [{}] {}\n{}: failed\n{}\n</code><br>'.format(
                    result.task_name, '*' * 100, host, self.callback._dump_results(result._result))
                results_raw.append(data)

        for task_obj in self.callback.task_skipped:
            for host, result in task_obj.items():
                data = '<code style="color: #FFFF00">TASK [{}] {}\n{}: skipped\n{}\n</code><br>'.format(
                    result.task_name, '*' * 100, host, self.callback._dump_results(result._result))
                results_raw.append(data)

        for task_obj in self.callback.task_unreachable:
            for host, result in task_obj.items():
                data = '<code style="color: #FF0000">TASK [{}] {}\n{}: unreachable\n{}\n</code><br>'.format(
                    result.task_name, '*' * 100, host, self.callback._dump_results(result._result))
                results_raw.append(data)

        task_status = 'PLAY RECAP {}\n'.format('*' * 100)
        for host, status in self.callback.task_status.items():
            task_status = task_status + '{} :{}\n'.format(host, status)
        results_raw.append(task_status)
        return results_raw

    @staticmethod
    def handle_setup_data(data):
        """处理setup模块数据，用于收集服务器信息功能"""
        server_facts = {}
        result = json.loads(data[data.index('{'): data.rindex('}') + 1])
        facts = result['ansible_facts']
        server_facts['hostname'] = facts['ansible_hostname']
        server_facts['cpu_model'] = facts['ansible_processor'][-1]
        server_facts['cpu_number'] = int(facts['ansible_processor_count'])
        server_facts['vcpu_number'] = int(facts['ansible_processor_vcpus'])
        server_facts['disk_total'], disk_size = 0, 0
        for k, v in facts['ansible_devices'].items():
            if k[0:2] in ['sd', 'hd', 'ss', 'vd']:
                if 'G' in v['size']:
                    disk_size = float(v['size'][0: v['size'].rindex('G') - 1])
                elif 'T' in v['size']:
                    disk_size = float(v['size'][0: v['size'].rindex('T') - 1]) * 1024
                server_facts['disk_total'] += round(disk_size, 2)
        server_facts['ram_total'] = round(int(facts['ansible_memtotal_mb']) / 1024)
        server_facts['kernel'] = facts['ansible_kernel']
        server_facts['system'] = '{} {} {}'.format(facts['ansible_distribution'],
                                                   facts['ansible_distribution_version'],
                                                   facts['ansible_userspace_bits'])
        server_model = facts['ansible_product_name']

        # 获取网卡信息
        nks = []
        for nk in facts.keys():
            networkcard_facts = {}
            if re.match(r"^ansible_(eth|bind|eno|ens|em)\d+?", nk):
                networkcard_facts['network_card_name'] = facts.get(nk).get('device')
                networkcard_facts['network_card_mac'] = facts.get(nk).get('macaddress')
                networkcard_facts['network_card_ip'] = facts.get(nk).get('ipv4').get('address') if 'ipv4' in facts.get(
                    nk) else 'unknown'
                networkcard_facts['network_card_model'] = facts.get(nk).get('type')
                networkcard_facts['network_card_mtu'] = facts.get(nk).get('mtu')
                networkcard_facts['network_card_status'] = 1 if facts.get(nk).get('active') else 0
                nks.append(networkcard_facts)
        return server_facts, server_model, nks

    @staticmethod
    def handle_mem_data(data):
        result = json.loads(data[data.index('{'): data.rindex('}') + 1])
        facts = result['ansible_facts']
        return facts['mem_info']
