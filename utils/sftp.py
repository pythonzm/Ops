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
import paramiko


class SFTP:
    def __init__(self, host, port, username, password=None, key_file=None):
        self.transport = paramiko.Transport(sock="{}:{}".format(host, port))

        if key_file:
            private_key = paramiko.RSAKey.from_private_key_file(key_file)
            self.transport.connect(username=username, pkey=private_key)
        else:
            self.transport.connect(username=username, password=password)

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
            print(e)
        finally:
            self.transport.close()

    def get_file(self, remote_file, local_file):
        try:
            self.sftp.get(remote_file, local_file)
        except Exception as e:
            print(e)
        finally:
            self.transport.close()
