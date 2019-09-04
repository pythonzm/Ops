# -*- coding: utf-8 -*-
"""
-------------------------------------------------
   File Name：      gen_resource
   Description:
   Author:          Administrator
   date：           2018-12-11
-------------------------------------------------
   Change Activity:
                    2018-12-11:
-------------------------------------------------
"""
from assets.models import ServerAssets
from utils.crypt_pwd import CryptPwd
from task.models import AnsibleInventory


class GenResource:
    @staticmethod
    def gen_host_list(host_ids):
        """
        生成格式为：[{"ip": "10.0.0.0", "port": "22", "username": "test", "password": "pass"}, ...]
        :return:
        """
        host_list = []
        for host_id in host_ids:
            host = {}
            host_obj = ServerAssets.objects.get(id=host_id)
            host['ip'] = host_obj.assets.asset_management_ip
            host['port'] = int(host_obj.port)
            host['username'] = host_obj.username
            host['password'] = CryptPwd().decrypt_pwd(host_obj.password)
            if host_obj.host_vars:
                host_vars = eval(host_obj.host_vars)
                for k, v in host_vars.items():
                    host[k] = v
            host_list.append(host)
        return host_list

    def gen_group_dict(self, group_ids):
        """
        生成格式为:
        {
                "group1": {
                    "hosts": [{"ip": "10.0.0.0", "port": "22", "username": "test", "password": "pass"}, ...],
                    "group_vars": {"var1": value1, "var2": value2, ...}
                }
            }
        :return:
        """
        resource = {}
        group_names = []
        for group_id in group_ids:
            group_values = {}
            group_obj = AnsibleInventory.objects.prefetch_related('ans_group_hosts').get(id=group_id)
            group_names.append(group_obj.ans_group_name)
            host_ids = [host.id for host in group_obj.ans_group_hosts.all()]
            group_values['hosts'] = self.gen_host_list(host_ids)
            if group_obj.ans_group_vars:
                group_values['group_vars'] = eval(group_obj.ans_group_vars)
            resource[group_obj.ans_group_name] = group_values
        return resource, group_names

    @staticmethod
    def gen_host_dict(group_ids):
        """
        生成所选主机组内的主机地址, 生成格式是[{'host_id': host.id, 'host_ip': host.ip}, {...}]
        :return:
        """
        hosts_temp = []
        for group_id in group_ids:
            host_list = AnsibleInventory.objects.prefetch_related('ans_group_hosts').get(
                id=group_id).ans_group_hosts.all()
            host_d = [{'host_id': host.id, 'host_ip': host.assets.asset_management_ip} for host in host_list]
            hosts_temp.extend(host_d)

        hosts = []
        for i in hosts_temp:
            if i not in hosts:
                hosts.append(i)

        return hosts
