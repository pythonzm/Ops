# -*- coding: utf-8 -*-
"""
-------------------------------------------------
   File Name：      utils
   Description:
   Author:          Administrator
   date：           2018/5/21
-------------------------------------------------
   Change Activity:
                    2018/5/21:
-------------------------------------------------
"""

import nmap
import telnetlib
import paramiko
from utils.init_yaml import Yaml
from conf.logger import scanhost_logger
from utils.crypt_pwd import CryptPwd


class ScanResults:
    def __init__(self):
        self.logger = scanhost_logger
        self.conf = Yaml('scanhosts.yaml').init_yaml()
        self.black_list = self.conf['hostinfo']['black_list']

    def scan_hosts(self, nets):
        """
        扫描指定网段内存活的主机
        :param nets: 网段，比如：10.1.19 或 10.1.19.0/24
        :type nets: list
        :rtype: list
        :return: 所有存活的主机
        """
        up_hosts = []
        self.logger.info('开始扫描')
        nm = nmap.PortScanner()
        for net in nets:
            nm.scan(net, arguments='-n -sP')

            for host in nm.all_hosts():
                if host not in self.black_list:
                    up_hosts.append(host)
        return up_hosts

    def scan_linux(self, hosts, port):
        """
        检测哪一台存活的主机是Linux主机
        :param hosts: 主机ip
        :param port: ssh端口
        :type port: int
        :return: 所有Linux主机
        :rtype: list
        """
        linux_hosts = []
        for host in hosts:
            try:
                tn = telnetlib.Telnet(host, port, timeout=5)
                if tn.read_until(b'ssh', timeout=5):
                    linux_hosts.append(host)
                    self.logger.info('{} 扫描成功,结果是Linux主机'.format(host))
            except Exception as e:
                self.logger.info('{} 扫描失败，原因：{}'.format(host, e))
        self.logger.info('获取Linux主机结束，开始尝试连接主机获取数据')
        return linux_hosts

    def get_results(self, host, port, user, cmds, password=None, keyfile=None):
        """
        登录Linux主机执行命令，保存的密码是加密后的密码
        :param host: 主机ip
        :param port: ssh端口
        :param user: 登录用户
        :param cmds: 执行的命令
        :param password: 登录密码
        :param keyfile: 密钥文件
        :type cmds: list
        :return: 包含host，user，password，cmd 的一个结果
        :rtype: dict
        """
        results = {}
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        c = CryptPwd()
        password = c.decrypt_pwd(password)
        try:
            ssh.connect(host, port, user, password)
            self.logger.info('初始化连接{}成功'.format(host))
            for cmd in cmds:
                if cmd == 'mac':
                    stdin, stdout, stderr = ssh.exec_command(self.conf['hostinfo']['syscmd_list'][cmd].format(host),
                                                             timeout=5)
                    res = stdout.read().decode('utf-8').strip()
                elif cmd == 'host_type':
                    stdin, stdout, stderr = ssh.exec_command(self.conf['hostinfo']['syscmd_list'][cmd], timeout=5)
                    stdin.write(password + '\n')
                    stdin.flush()
                    res = stdout.read().decode('utf-8').strip()
                    if res:
                        if cmd == 'host_type':
                            if 'Alibaba' in res:
                                res = 1
                            elif 'VMware' in res:
                                res = 2
                            else:
                                res = 0
                                host_ext = host.split('.')[-1]
                                public_ip = '210.51.161.{}'.format(host_ext)
                                results['public_ip'] = public_ip
                else:
                    stdin, stdout, stderr = ssh.exec_command(self.conf['hostinfo']['syscmd_list'][cmd], timeout=5)
                    if 'sudo' in self.conf['hostinfo']['syscmd_list'][cmd]:
                        stdin.write(password + '\n')
                        stdin.flush()
                    res = stdout.read().decode('utf-8').strip()
                if res is not None:
                    results['internal_ip'] = host
                    results[cmd] = res
                    results['ssh_user'] = user
                    results['ssh_passwd'] = c.encrypt_pwd(password)
                    results['ssh_port'] = port
                    self.logger.info('获取{}的 {} 数据完成！'.format(host, cmd))
                else:
                    self.logger.error('请确认{}上安装了{},并且{}已经配置在了sudo文件中'.format(host, cmd, user))
            return results
        except Exception as e:
            self.logger.error('初始化连接{}失败，原因：{}'.format(host, e))
        finally:
            ssh.close()

