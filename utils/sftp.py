# -*- coding: utf-8 -*-
"""
-------------------------------------------------
   File Name：      sftp
   Description:
   Author:          Administrator
   date：           2018-10-25
-------------------------------------------------
   Change Activity:
                    2018-10-25:
-------------------------------------------------
"""
import os
import logging
import paramiko
from django.http import FileResponse
from django.utils.http import urlquote


class SFTP:
    def __init__(self, host, port, username, password=None, key_file=None):
        self.username = username
        self.transport = paramiko.Transport(sock="{}:{}".format(host, port))

        if key_file:
            private_key = paramiko.RSAKey.from_private_key_file(key_file)
            self.transport.connect(username=self.username, pkey=private_key)
        else:
            self.transport.connect(username=self.username, password=password)

        self.sftp = paramiko.SFTPClient.from_transport(self.transport)

    def put_file(self, local_file, user_home):
        """
        user_home指用户的家目录，比如：/home/zz，主要用于获取用户的uid和gid
        :param local_file: 本地文件的路径
        :param user_home: 远程服务器登录用户的家目录，路径最后没有"/"
        """
        try:
            filename = local_file.split('/')[-1]
            remote_file = '{}/{}'.format(user_home, filename)
            self.sftp.put(local_file, remote_file)
            file_stat = self.sftp.stat(user_home)
            self.sftp.chown(remote_file, file_stat.st_uid, file_stat.st_gid)
        except Exception as e:
            logging.getLogger().error(e)
        finally:
            self.transport.close()

    def get_file(self, remote_file, local_file):
        try:
            self.sftp.get(remote_file, local_file)
        except Exception as e:
            logging.getLogger().error(e)
        finally:
            self.transport.close()

    def download_file(self, download_file, download_file_path):

        local_file_name = download_file.split('/')[-1]

        if not os.path.exists(download_file_path):
            os.makedirs(download_file_path, exist_ok=True)

        local_file = '{}/{}'.format(download_file_path, local_file_name)

        download_file_size = self.sftp.stat(download_file).st_size

        self.get_file(download_file, local_file)

        local_file_size = None
        while local_file_size != download_file_size:
            local_file_size = os.path.getsize(local_file)

        response = FileResponse(open(local_file, 'rb'))
        response['Content-Type'] = 'application/octet-stream'
        response['Content-Disposition'] = 'attachment;filename="{filename}"'.format(filename=urlquote(local_file_name))
        return response

    def upload_file(self, upload_file, upload_file_path):
        if not os.path.exists(upload_file_path):
            os.makedirs(upload_file_path, exist_ok=True)

        local_file = '{}/{}'.format(upload_file_path, upload_file.name)

        if not os.path.exists(local_file):
            open(local_file, 'w').close()
        local_file_size = None

        while local_file_size != upload_file.size:
            with open(local_file, 'wb') as f:
                for chunk in upload_file.chunks():
                    f.write(chunk)
            local_file_size = os.path.getsize(local_file)

        if self.username == 'root':
            self.put_file(local_file, '/root/')
        else:
            self.put_file(local_file, '/home/{}'.format(self.username))
