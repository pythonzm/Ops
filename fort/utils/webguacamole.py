from utils.guacamole import MyGuacamole
from assets.models import ServerAssets
from fort.models import FortServerUser


class GuacamoleConsumer(MyGuacamole):
    def __init__(self, *args, **kwargs):
        super(GuacamoleConsumer, self).__init__(*args, **kwargs)
        self.fort_server = ServerAssets.objects.select_related('assets').get(id=self.scope['path'].split('/')[3])
        self.fort_user = FortServerUser.objects.get(id=self.scope['path'].split('/')[4])
        self.ip = self.fort_server.assets.asset_management_ip
        self.username = self.fort_user.fort_username
        self.password = self.fort_user.fort_password

    def connect(self):
        if self.scope["user"].is_anonymous:
            self.close(code=1007)
        else:
            self.accept('guacamole')

        server_protocol = self.fort_user.fort_server.server_protocol
        if server_protocol == 'vnc':
            self.client.handshake(protocol=server_protocol,
                                  hostname=self.ip,
                                  port=self.fort_user.fort_vnc_port,
                                  password=self.password, width=self.width, height=self.height,
                                  dpi=self.dpi)
        elif server_protocol == 'rdp':
            self.client.handshake(protocol=server_protocol,
                                  hostname=self.ip, port=self.fort_server.port,
                                  password=self.fort_user.fort_password,
                                  username=self.username, width=self.width, height=self.height, dpi=self.dpi)
        self.send('0.,{0}.{1};'.format(len(self.group_name), self.group_name))
        self.guacamole_thread.setDaemon(True)
        self.guacamole_thread.start()
