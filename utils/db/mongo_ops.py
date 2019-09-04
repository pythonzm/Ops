# -*- coding: utf-8 -*-
"""
-------------------------------------------------
   File Name：      mongo_ops
   Description:
   Author:          pythonzm
   date：           2018/6/3
-------------------------------------------------
   Change Activity:
                    2018/6/3:
-------------------------------------------------
"""
import json
import pymongo
from urllib import parse
from bson import ObjectId
from datetime import date, datetime


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


class MongoOps:
    def __init__(self, host, port, db, coll, username=None, password=None, authSource='admin'):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.authSource = authSource
        self.client = self.__client()
        self.db = self.client[db]
        self.coll = self.db[coll]

    def __client(self):
        if self.username and self.password:
            self.username = parse.quote_plus(self.username)
            self.password = parse.quote_plus(self.password)
            uri = "mongodb://{}:{}@{}:{}/?authSource={}".format(self.username, self.password, self.host, self.port,
                                                                self.authSource)
            client = pymongo.MongoClient(uri)
        else:
            client = pymongo.MongoClient(self.host, self.port)
        return client

    def insert_one(self, content):
        """
        :type content: dict
        :return:
        """
        self.coll.insert_one(content)

    def insert_many(self, content_list):
        """
        :param content_list: [{'x': 1}, {'x': 2}]
        :type content_list: list
        :return:
        """
        self.coll.insert_many(content_list)

    def find(self, query_dict=None, skip=0, limit=0, sort_key=None, sort_method=1):
        """
        :param query_dict: 字典形式，比如：{"name": "xxx"} {"count": {"$gt": 100}}
        :param skip
        :param limit
        :type query_dict: dict
        :rtype: list
        """
        if sort_key:
            if query_dict:
                r = self.coll.find(query_dict).sort(sort_key, sort_method).skip(skip).limit(limit)
            else:
                r = self.coll.find().sort(sort_key, sort_method).skip(skip).limit(limit)
        else:
            if query_dict:
                r = self.coll.find(query_dict).skip(skip).limit(limit)
            else:
                r = self.coll.find().skip(skip).limit(limit)

        results = [i for i in r]
        count = len(results)
        return results, count

    def delete(self, condition, del_all=True):
        """
        :param condition: {"name": "xxx"}
        :type condition: dict
        :param del_all: 是否将匹配到的结果全部删除,False: 只删除一条匹配到的结果
        :type del_all: bool
        :return:
        """
        if del_all:
            self.coll.delete_many(condition)
        else:
            self.coll.delete_one(condition)

    def close(self):
        self.client.close()

    def json_res(self, data):
        """
        用于将mongo数据进行JSON序列化
        :param data: mongo数据
        :return: JSON数据
        """
        res = JSONEncoder().encode(data)
        return res
