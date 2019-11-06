# -*- coding: utf-8 -*-
from fort.models import FortServerUser
from assets.models import ServerAssets
from utils.ssh import MySSH


class FortConsumer(MySSH):
    def __init__(self, *args, **kwargs):
        super(FortConsumer, self).__init__(*args, **kwargs)
        self.fort_server = ServerAssets.objects.select_related('assets').get(id=self.scope['path'].split('/')[3])
        self.fort_user = FortServerUser.objects.get(id=self.scope['path'].split('/')[4])
        self.ip = self.fort_server.assets.asset_management_ip
        self.port = self.fort_server.port
        self.username = self.fort_user.fort_username
        self.password = self.fort_user.fort_password
