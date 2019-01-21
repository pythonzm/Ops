# -*- coding: utf-8 -*-
"""
-------------------------------------------------
   File Name：      redis_ops
   Description:
   Author:          Administrator
   date：           2018-06-29
-------------------------------------------------
   Change Activity:
                    2018-06-29:
-------------------------------------------------
"""
# -*- coding=utf-8 -*-
import redis
from conf.logger import ansible_logger


class RedisOps:
    def __init__(self, host, port, db, password=None):
        pool = redis.ConnectionPool(host=host, port=port, db=db, password=password, decode_responses=True)
        self.redis_conn = redis.StrictRedis(connection_pool=pool)
        self.r = self.redis_conn.pubsub()

    def lpush(self, rediskey, *values):
        """
        在rediskey对应的list中添加元素每个新的元素都添加到列表的头部
        :param rediskey:
        :return:
        """
        try:
            self.redis_conn.lpush(rediskey, *values)
        except Exception as e:
            ansible_logger.error("添加数据失败：{}".format(e))

    def lpop(self, rediskey):
        """
        移除并返回列表的第一个元素
        :param rediskey:
        :return:
        """
        try:
            data = self.redis_conn.lpop(rediskey)
            return data
        except Exception as e:
            ansible_logger.error("获取数据（lpop）失败：{}".format(e))

    def rpush(self, rediskey, *values):
        """
        在rediskey对应的list中添加元素每个新的元素都添加到列表的尾部
        :param rediskey:
        :return:
        """
        try:
            self.redis_conn.rpush(rediskey, *values)
        except Exception as e:
            ansible_logger.error("添加数据失败：{}".format(e))

    def rpop(self, rediskey):
        """
        移除并返回列表的最后一个元素
        :param rediskey:
        :return:
        """
        try:
            data = self.redis_conn.rpop(rediskey)
            return data
        except Exception as e:
            ansible_logger.error("获取数据（rpop）失败：{}".format(e))

    def lrange(self, rediskey):
        """
        获取列表中所有数据
        :param rediskey:
        :return:
        """
        try:
            data = self.redis_conn.lrange(rediskey, 0, -1)
            return data
        except Exception as e:
            ansible_logger.error("获取数据（lrange）失败：{}".format(e))

    def delete(self, *args):
        try:
            self.redis_conn.delete(*args)
        except Exception as e:
            ansible_logger.error("删除数据失败：{}".format(e))

    def set(self, rediskey, value):
        try:
            self.redis_conn.set(rediskey, value)
        except Exception as e:
            ansible_logger.error("设置数据失败：{}".format(e))

    def mset(self, **kwargs):
        try:
            data = self.redis_conn.mset(**kwargs)
            return data
        except Exception as e:
            ansible_logger.error("设置数据失败：{}".format(e))

    def get(self, rediskey):
        try:
            data = self.redis_conn.get(rediskey)
            return data
        except Exception as e:
            ansible_logger.error("获取数据（get）失败：{}".format(e))

    def mget(self, *args):
        try:
            data = self.redis_conn.mget(*args)
            return data
        except Exception as e:
            ansible_logger.error("获取多个数据（mget）失败：{}".format(e))

    def sadd(self, rediskey, *values):
        try:
            self.redis_conn.sadd(rediskey, *values)
        except Exception as e:
            ansible_logger.error("设置数据集合失败：{}".format(e))

    def smembers(self, rediskey):
        try:
            data = self.redis_conn.smembers(rediskey)
            return data
        except Exception as e:
            ansible_logger.error("获取数据集合失败：{}".format(e))

    def publish(self, channel, message):
        self.redis_conn.publish(channel, message)

    def subscribe(self, channel, *args, **kwargs):
        self.r.subscribe(channel, *args, **kwargs)
        return self.r.listen()

    def unsubscribe(self, channel):
        self.r.unsubscribe(channel)

    def sub_message(self, channel):
        self.r.subscribe(channel)
        return self.r.get_message(ignore_subscribe_messages=True)
