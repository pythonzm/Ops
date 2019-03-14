# -*- coding: utf-8 -*-
"""
-------------------------------------------------
   File Name：      init_yaml
   Description:
   Author:          Administrator
   date：           2018/6/3
-------------------------------------------------
   Change Activity:
                    2018/6/3:
-------------------------------------------------
"""
from django.conf import settings
import yaml


class Yaml:
    def __init__(self, filename):
        self.file = '{}/conf/{}'.format(settings.BASE_DIR, filename)

    def init_yml(self):
        """
        初始化yaml文件
        :return: 初始化后的内容
        :rtype: dict
        """
        with open(self.file) as yml_file:
            conf = yaml.load(yml_file)
            return conf
