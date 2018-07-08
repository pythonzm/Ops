# -*- coding: utf-8 -*-
"""
-------------------------------------------------
   File Name：      get_mongo_log
   Description:
   Author:          Administrator
   date：           2018/6/3
-------------------------------------------------
   Change Activity:
                    2018/6/3:
-------------------------------------------------
"""
import json
from bson import ObjectId
from datetime import date, datetime
import pymongo
from utils.init_yaml import Yaml


class JSONEncoder(json.JSONEncoder):
    """
    用于JSON序列化mongodb中的_id和date对象以及datetime对象
    """

    def default(self, o):
        if isinstance(o, ObjectId):
            return str(o)
        elif isinstance(o, datetime):
            return o.strftime('%Y-%m-%d %H:%M:%S')
        elif isinstance(o, date):
            return o.strftime('%Y-%m-%d')
        return json.JSONEncoder.default(self, o)


def get_mongo_json_log(data):
    """
    用于将mongo数据进行JSON序列化
    :param data: mongo数据
    :return: JSON数据
    """
    res = JSONEncoder().encode(data)
    return res


class MongoLog:
    """
    初始化用于存储日志的collection
    :param coll: 用于存储日志的collection名称
    """

    def __init__(self, coll):
        self.conf = Yaml('mongo.yaml').init_yaml()
        self.client = pymongo.MongoClient(self.conf['mongod']['HOST'], self.conf['mongod']['PORT'])
        self.db = self.client[self.conf['mongod']['DB']]
        self.coll = self.db[self.conf['mongod'][coll]]

    def insert(self, content):
        """
        将日志写入mongodb
        :param content: 日志内容
        :type content: dict
        :return:
        """
        return self.coll.insert(content)

    def find(self):
        """
        获取所有日志记录
        :return: 所有日志记录
        :rtype: list
        """
        r = self.coll.find().sort("time", -1)
        return list(r)

    def delete(self):
        """
        删除所有日志记录
        :return:
        """
        return self.coll.remove({})
