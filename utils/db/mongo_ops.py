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
from utils.init_yml import Yaml


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


def get_mongo_json_res(data):
    """
    用于将mongo数据进行JSON序列化
    :param data: mongo数据
    :return: JSON数据
    """
    res = JSONEncoder().encode(data)
    return res


class MongoOps:
    def __init__(self, host, port, db, coll):
        self.client = pymongo.MongoClient(host, port)
        self.db = self.client[db]
        self.coll = self.db[coll]

    def insert(self, content):
        """
        将日志写入mongodb
        :type content: dict
        :return:
        """
        return self.coll.insert(content)

    def find(self, query_dict=None):
        """
        获取所有日志记录
        :param query_dict: 字典形式，比如：{"name": "xxx"}
        :type query_dict: dict
        :return: 所有日志记录
        :rtype: list
        """
        if query_dict:
            r = self.coll.find(query_dict)
        else:
            r = self.coll.find()
        return list(r)

    def delete(self):
        """
        删除所有日志记录
        :return:
        """
        return self.coll.remove({})
