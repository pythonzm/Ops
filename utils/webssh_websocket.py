from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer
from assets.models import ServerAssets
from fort.models import FortServerUser
from utils.db.redis_ops import RedisOps
from Ops import settings
from utils.db.mongo_ops import MongoOps, get_mongo_json_res
import paramiko
import threading
import time

c = RedisOps(settings.REDIS_HOST, settings.REDIS_PORT, db=6)


class MyThread(threading.Thread):
    def __init__(self, chan):
        super(MyThread, self).__init__()
        self.chan = chan

    def run(self):
        while not self.chan.chan.exit_status_ready():
            try:
                data = self.chan.chan.recv(1024)
                if data:
                    str_data = bytes.decode(data)
                    self.send_msg(str_data)
            except Exception:
                pass
        self.send_msg('\r\n已成功登出，刷新页面重新登录，关闭页面断开连接')
        c.rpush('commands', 'logout')
        self.chan.ssh.close()

    def send_msg(self, msg):
        async_to_sync(self.chan.channel_layer.group_send)(
            self.chan.channel_name,
            {
                "type": "user.message",
                "text": msg
            },
        )


def record_command(login_user, fort):
    mongo = MongoOps(settings.MONGODB_HOST, settings.MONGODB_PORT, settings.COMMANDS_DB, coll=login_user)
    a = ''
    while True:
        command = c.lpop('commands')
        if command == '\r':
            content = {'fort': fort, 'command': a.strip(),
                       'datetime': get_mongo_json_res(time.strftime(settings.TIME_FORMAT))}
            mongo.insert(content)
            a = ''
            continue
        elif command == 'logout':
            break
        else:
            a += command


class SSHConsumer(WebsocketConsumer):

    def connect(self):
        path = self.scope['path']
        server_id = path.split('/')[3]
        fort_user_id = path.split('/')[4]
        host = ServerAssets.objects.select_related('assets').get(id=server_id)
        fort_user = FortServerUser.objects.get(id=fort_user_id)
        self.host_ip = host.assets.asset_management_ip
        host_port = int(host.port)
        self.username = fort_user.fort_username
        password = fort_user.fort_password
        # 创建channels group， 命名为：用户名，并使用channel_layer写入到redis
        async_to_sync(self.channel_layer.group_add)(self.channel_name, self.channel_name)
        self.ssh = paramiko.SSHClient()
        self.ssh.load_system_host_keys()
        self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.ssh.connect(self.host_ip, host_port, self.username, password)
        self.chan = self.ssh.invoke_shell(term='xterm')
        self.chan.settimeout(0)
        t1 = MyThread(self)
        t1.setDaemon(True)
        t1.start()
        # 返回给receive方法处理
        self.accept()

    def receive(self, text_data=None, bytes_data=None):
        self.chan.send(text_data)
        c.rpush('commands', text_data)

    def user_message(self, event):
        self.send(text_data=event["text"])
        if '登出' in event["text"]:
            t2 = threading.Thread(target=record_command,
                                  args=(self.scope['user'].username, '{}@{}'.format(self.username, self.host_ip)))
            t2.setDaemon(True)
            t2.start()

    def disconnect(self, close_code):
        async_to_sync(self.channel_layer.group_discard)(self.channel_name, self.channel_name)
