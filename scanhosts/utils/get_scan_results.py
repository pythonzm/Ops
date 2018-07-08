# -*- coding: utf-8 -*-
"""
-------------------------------------------------
   File Name：      get_results
   Description:
   Author:          Administrator
   date：           2018/5/24
-------------------------------------------------
   Change Activity:
                    2018/5/24:
-------------------------------------------------
"""
from scanhosts.utils.scan_host import ScanResults


def get_scan_results():
    """
    获取所有扫描成功的主机的硬件信息
    :return: 主机的硬件信息
    :rtype: list
    """
    results = []
    begin_scan = ScanResults()
    nets = begin_scan.conf['hostinfo']['nets']
    cmds = begin_scan.conf['hostinfo']['syscmd_list'].keys()
    port = begin_scan.conf['hostinfo']['port']
    user = begin_scan.conf['hostinfo']['ssh_user']
    passwords = begin_scan.conf['hostinfo']['ssh_pass']

    up_hosts = begin_scan.scan_hosts(nets)
    linux_hosts = begin_scan.scan_linux(up_hosts, port)

    for host in linux_hosts:
        for password in passwords:
            result = begin_scan.get_results(host=host, port=port, user=user, cmds=cmds, password=password)
            if result:
                results.append(result)

    return results
