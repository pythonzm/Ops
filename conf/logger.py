# -*- coding: utf-8 -*-
"""
-------------------------------------------------
   File Name：      logger
   Description:
   Author:          Administrator
   date：           2018/6/2
-------------------------------------------------
   Change Activity:
                    2018/6/2:
-------------------------------------------------
"""
import logging
from logging.config import fileConfig
from django.conf import settings
import os

logger_file = os.path.join(settings.BASE_DIR, 'conf', 'logger.conf')

fileConfig(logger_file)
ansible_logger = logging.getLogger('ansible')
user_logger = logging.getLogger('user')
fort_logger = logging.getLogger('fort')
deploy_logger = logging.getLogger('deploy')
