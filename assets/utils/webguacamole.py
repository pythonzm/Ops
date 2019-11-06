# -*- coding: utf-8 -*-
"""
-------------------------------------------------
   File Name：      root_rdp
   Description:
   Author:          Administrator
   date：           2019-01-21
-------------------------------------------------
   Change Activity:
                    2019-01-21:
-------------------------------------------------
"""
from utils.guacamole import MyGuacamole
from utils.crypt_pwd import CryptPwd
from assets.models import ServerAssets


class AdminGuacamole(MyGuacamole):
    def __init__(self, *args, **kwargs):
        super(AdminGuacamole, self).__init__(*args, **kwargs)
        self.server = ServerAssets.objects.select_related('assets').get(id=self.scope['path'].split('/')[3])
        self.ip = self.server.assets.asset_management_ip
        self.port = self.server.port
        self.username = self.server.username
        self.password = CryptPwd().decrypt_pwd(self.server.password)
