# -*- coding: utf-8 -*-
from utils.ssh import MySSH
from utils.crypt_pwd import CryptPwd
from assets.models import ServerAssets


class SSHConsumer(MySSH):
    def __init__(self, *args, **kwargs):
        super(SSHConsumer, self).__init__(*args, **kwargs)
        self.server = ServerAssets.objects.select_related('assets').get(id=self.scope['path'].split('/')[3])
        self.ip = self.server.assets.asset_management_ip
        self.port = self.server.port
        self.username = self.server.username
        self.password = CryptPwd().decrypt_pwd(self.server.password)
