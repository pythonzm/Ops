# -*- coding: utf-8 -*-
"""
-------------------------------------------------
   File Name：      get_verbose_name
   Description:
   Author:          Administrator
   date：           2018/6/10
-------------------------------------------------
   Change Activity:
                    2018/6/10:
-------------------------------------------------
"""


def get_model_fields(model_name):
    """
    主要获取Model中设置的verbose_name
    :param model_name: Model的名称，即django的model对象，区分大小写
    :return: 返回值包括字段名以及其verbose_name,两者组成字典
    :rtype: dict
    """
    fileds = model_name._meta.fields
    field_dic = {}
    for i in fileds:
        field_dic[i.name] = i.verbose_name
    return field_dic
