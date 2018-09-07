# -*- coding: utf-8 -*-
"""
-------------------------------------------------
   File Name：      zabbix_api
   Description:
   Author:          Administrator
   date：           2018-08-24
-------------------------------------------------
   Change Activity:
                    2018-08-24:
-------------------------------------------------
"""
import requests
import json
import uuid
import os
from Ops import settings


class ZabbixApi(object):
    def __init__(self, api_url, username, password):
        self.api_url = api_url
        self.username = username
        self.password = password
        self.header = {"Content-Type": "application/json"}
        self.auth_token = None

    def request(self, method, params, request_id=1):
        """
        Send request to Zabbix API
        :param request_id: 请求ID
        :param method: Zabbix API 请求方法
        :param params: Zabbix API 请求参数
        :return: json
        """
        data = json.dumps({"jsonrpc": "2.0",
                           "method": method,
                           "params": params,
                           "auth": self.auth_token,
                           "id": request_id})
        req = requests.post(self.api_url, data=data, headers=self.header)
        request_id += 1
        try:
            return json.loads(req.text)["result"]
        except:
            return json.loads(req.text)["error"]

    def login(self):
        method = "user.login"
        params = {
            "user": self.username,
            "password": self.password
        }
        req = self.request(method, params)
        self.auth_token = req

    def get_host(self, host_name=None, host_ip=None, search=None):
        method = "host.get"
        params = {
            "output": "hostid",
            "selectGroups": "extend",
            "filter": {
                "host": host_name,
                "ip": host_ip
            }
        }
        if search:
            params.update({"search": {
                "host": [search],
            }})
        req = self.request(method, params)

        host_id = req[0]['hostid']
        group_id = req[0]['groups'][0]['groupid']
        return host_id, group_id

    def create_host(self, host_name, hostgroups, templates, host_ip):
        if self.get_host(host_name=host_name):
            return {"code": "10001", "message": "The host was added!"}

        group_list = [{"groupid": hostgroup_id} for hostgroup_id in hostgroups]
        template_list = [{"templateid": templete_id} for templete_id in templates]

        method = "host.create"
        params = {
            "host": host_name,
            "interfaces": [
                {
                    "type": 1,
                    "main": 1,
                    "useip": 1,
                    "ip": host_ip,
                    "dns": "",
                    "port": "10050"
                }
            ],
            "groups": group_list,
            "templates": template_list,
        }
        req = self.request(method, params)
        return req

    def update_host(self, host_id, host_name=None, hostgroups=None, templates_clear=None, host_ip=None):
        """
        zabbix api更新主机模板时，主机名对模板中的一些item有依赖，无法正常更新主机，这个update用起来很不方便
        """
        group_list = [{"groupid": hostgroup_id} for hostgroup_id in hostgroups]
        templates_clear_list = [{"templateid": templete_id} for templete_id in templates_clear]

        method = "host.update"
        params = {
            "hostid": host_id,
            "host": host_name,
            "interfaces": [
                {
                    "type": 1,
                    "main": 1,
                    "useip": 1,
                    "ip": host_ip,
                    "dns": "",
                    "port": "10050"
                }
            ],
            "groups": group_list,
            "templates_clear": templates_clear_list,
        }
        req = self.request(method, params)
        return req

    def delete_host(self, host_ids):
        """
        :param host_ids: 主机ID
        :type host_ids: list
        :return:
        """
        method = "host.delete"
        params = host_ids
        req = self.request(method, params)
        return req

    def get_hostgroups(self, hostgroupName):
        """
        :param hostgroupName: 主机组名称
        :type hostgroupName: list
        :return:
        """
        method = "hostgroup.get"
        params = {
            "output": "extend",
            "selectHosts": "extend",
            "filter": {
                "name": hostgroupName
            }
        }
        req = self.request(method, params)
        return req

    def create_hostgroup(self, hostgroupName):
        if self.get_hostgroups([hostgroupName]):
            return {"code": "10002", "message": "The hostgroup was added!"}

        method = "hostgroup.create"
        params = {"name": hostgroupName}
        req = self.request(method, params)
        return req

    def get_templetes(self, templateName):
        """
        :param templateName:
        :type templateName: list
        :return:
        """
        method = "template.get"
        params = {
            "output": "extend",
            "filter": {
                "name": templateName
            }
        }
        req = self.request(method, params)
        return req

    def get_graph(self, host_id):
        method = "graph.get"
        params = {
            "output": "extend",
            "hostids": host_id,
            "sortfield": "name"
        }
        req = self.request(method, params)
        return req

    def save_graph(self, login_url, base_url, graphid):
        user_agent = 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.87 Safari/537.36'
        headers = {'User-Agent': user_agent}
        login_info = {
            'name': self.username,
            'password': self.password,
            'autologin': 1,
            'enter': 'Sign in'
        }
        s = requests.session()
        s.post(login_url, data=login_info, headers=headers)

        payload = {'graphid': graphid, 'width': 500, 'height': 200, 'period': 3600}
        res = s.get(base_url, params=payload, headers=headers)
        graph_path = os.path.join(settings.MEDIA_ROOT, 'zabbix')
        graph_name = '{}.jpg'.format(uuid.uuid4())
        graph = '{}/{}'.format(graph_path, graph_name)
        if not os.path.exists(graph_path):
            os.makedirs(graph_path)
        with open(graph, 'wb') as f:
            f.write(res.content)

        if os.path.exists(graph):
            graph_name = 'zabbix/{}'.format(graph_name)
            return graph_name
