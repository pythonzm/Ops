# -*- coding: utf-8 -*-
"""
-------------------------------------------------
   File Name：      wx_alert
   Description:
   Author:          Administrator
   date：           2018-12-10
-------------------------------------------------
   Change Activity:
                    2018-12-10:
-------------------------------------------------
"""
import requests
import logging
import json


class WxApi:
    def __init__(self, corp_id, corp_secret):
        self.corp_id = corp_id
        self.corp_secret = corp_secret
        self.token = self.get_token()

    def get_token(self):
        gettoken_url = 'https://qyapi.weixin.qq.com/cgi-bin/gettoken?corpid=' + self.corp_id + '&corpsecret=' + self.corp_secret
        try:
            res = requests.get(gettoken_url)
            token = res.json().get('access_token')
            return token
        except Exception as e:
            logging.getLogger().warning(e)

    def send_msg(self, subject, content):
        send_url = 'https://qyapi.weixin.qq.com/cgi-bin/message/send?access_token=' + self.token
        send_data = {
            "toparty": "3",
            "msgtype": "text",
            "agentid": 1,
            "text": {
                "content": subject + '\n' + content
            },
            "safe": 0
        }

        res = requests.post(send_url, data=json.dumps(send_data)).json()

        if res.get('errcode') != 0:
            logging.getLogger().error('错误码：{}, 错误信息：{}'.format(res.get('errcode'), res.get('errmsg')))
