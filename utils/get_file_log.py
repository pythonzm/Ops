# -*- coding: utf-8 -*-
"""
-------------------------------------------------
   File Name：      get_file_log
   Description:
   Author:          Administrator
   date：           2018/6/3
-------------------------------------------------
   Change Activity:
                    2018/6/3:
-------------------------------------------------
"""
import subprocess
from conf.logger import scanhost_logger


def get_log_content(log_file):
    """
    获取日志文件最后一行的内容
    :param log_file: 日志文件
    :return:
    """
    try:
        line_nu = subprocess.getoutput("wc -l {} | cut -d' ' -f1".format(log_file))
        if line_nu == '0':
            line_nu = '1'
        log_content = subprocess.getoutput('sed -n "{}p" {}'.format(line_nu, log_file))
        return log_content
    except Exception as e:
        scanhost_logger.error('获取日志内容出错，原因：{}'.format(e))
