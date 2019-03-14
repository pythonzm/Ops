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
from django.conf import settings


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
        return host_id

    def get_item(self, hostids):
        method = "item.get"
        params = {
            "output": "extend",
            "hostids": hostids,
            "search": {
                'key_': ['system.cpu.load', 'vm.memory', 'net']
            },
            'searchByAny': True,
            "sortfield": "name"
        }
        res = self.request(method, params)
        return res

    def get_history(self, itemids, history=3):
        method = "history.get"
        params = {
            "output": "extend",
            "history": history,
            "itemids": itemids,
            "sortfield": "clock",
            "sortorder": "DESC",
            "limit": 10
        }
        res = self.request(method, params)
        return res

    def get_alerts(self):
        method = "alert.get"
        params = {
            "countOutput": "1",
        },
        res = self.request(method, params)
        return res

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
