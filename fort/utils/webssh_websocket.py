import paramiko
import threading
import time
import os
import logging
from fort.tasks import fort_file
from socket import timeout
from channels.generic.websocket import WebsocketConsumer
from assets.models import ServerAssets
from fort.models import FortServerUser, FortRecord
from django.conf import settings


class MyThread(threading.Thread):
    def __init__(self, chan):
        super(MyThread, self).__init__()
        self.chan = chan
        self._stop_event = threading.Event()
        self.start_time = time.time()
        self.current_time = time.strftime(settings.TIME_FORMAT)
        self.stdout = []
        self.read_lock = threading.RLock()

    def stop(self):
        self._stop_event.set()

    def run(self):
        with self.read_lock:
            while not self._stop_event.is_set():
                time.sleep(0.1)
                try:
                    data = self.chan.chan.recv(1024)
                    if data:
                        str_data = bytes.decode(data)
                        self.chan.send(str_data)
                        self.stdout.append([time.time() - self.start_time, 'o', str_data])
                except timeout:
                    break
            self.chan.send('\n由于长时间没有操作，连接已断开!')
            self.stdout.append([time.time() - self.start_time, 'o', '\n由于长时间没有操作，连接已断开!'])
            self.chan.close()

    def record(self):
        record_path = os.path.join(settings.MEDIA_ROOT, 'ssh_records', self.chan.scope['user'].username,
                                   time.strftime('%Y-%m-%d'))
        if not os.path.exists(record_path):
            os.makedirs(record_path, exist_ok=True)
        record_file_name = '{}.{}.cast'.format(self.chan.fort, time.strftime('%Y%m%d%H%M%S'))
        record_file_path = os.path.join(record_path, record_file_name)

        header = {
            "version": 2,
            "width": self.chan.width,
            "height": self.chan.height,
            "timestamp": round(self.start_time),
            "title": "Demo",
            "env": {
                "TERM": os.environ.get('TERM'),
                "SHELL": os.environ.get('SHELL', '/bin/bash')
            },
        }

        fort_file.delay(record_file_path, self.stdout, header)

        login_status_time = time.time() - self.start_time
        if login_status_time >= 60:
            login_status_time = '{} m'.format(round(login_status_time / 60, 2))
        elif login_status_time >= 3600:
            login_status_time = '{} h'.format(round(login_status_time / 3660, 2))
        else:
            login_status_time = '{} s'.format(round(login_status_time))

        FortRecord.objects.create(
            login_user=self.chan.scope['user'],
            fort=self.chan.fort,
            remote_ip=self.chan.remote_ip,
            start_time=self.current_time,
            login_status_time=login_status_time,
            record_file=record_file_path.split('media/')[1],
            record_mode='ssh'
        )


class FortConsumer(WebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super(FortConsumer, self).__init__(*args, **kwargs)
        self.ssh = paramiko.SSHClient()
        self.fort_server = ServerAssets.objects.select_related('assets').get(id=self.scope['path'].split('/')[3])
        self.fort_user = FortServerUser.objects.get(id=self.scope['path'].split('/')[4])
        self.t1 = MyThread(self)
        self.width = 150
        self.height = 30
        self.remote_ip = self.scope['query_string'].decode('utf8')
        self.chan = None
        self.fort = None

    def connect(self):
        self.accept()

        host_ip = self.fort_server.assets.asset_management_ip
        username = self.fort_user.fort_username
        self.fort = r'{}@{}'.format(username, host_ip)

        try:
            self.ssh.load_system_host_keys()
            self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            self.ssh.connect(host_ip, int(self.fort_server.port), username, self.fort_user.fort_password, timeout=5)
        except Exception as e:
            logging.getLogger().error('用户{}通过webssh连接{}失败！原因：{}'.format(username, host_ip, e))
            self.send('用户{}通过webssh连接{}失败！原因：{}'.format(username, host_ip, e))
            self.close()
        self.chan = self.ssh.invoke_shell(term='xterm', width=self.width, height=self.height)
        # 设置如果3分钟没有任何输入，就断开连接
        self.chan.settimeout(60 * 3)
        self.t1.setDaemon(True)
        self.t1.start()

    def receive(self, text_data=None, bytes_data=None):
        self.chan.send(text_data)

    def disconnect(self, close_code):
        try:
            self.t1.record()
        finally:
            self.ssh.close()
            self.t1.stop()
