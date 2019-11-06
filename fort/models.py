from django.db import models


class FortServer(models.Model):
    server_status_ = (
        (0, '禁用'),
        (1, '正常'),
    )
    server_protocols = (
        ('ssh', 'ssh'),
        ('vnc', 'vnc'),
        ('rdp', 'rdp'),
    )
    server = models.OneToOneField('assets.ServerAssets', on_delete=models.CASCADE)
    server_protocol = models.CharField(max_length=3, choices=server_protocols, verbose_name='连接协议', default='ssh')
    server_status = models.SmallIntegerField(choices=server_status_, default=1, verbose_name='是否允许web登录')

    class Meta:
        db_table = 'ops_fort_server'
        permissions = (
            ("view_fortserver", "读取堡垒机权限"),
            ("ssh_fortserver", "连接主机权限"),
        )
        verbose_name = '堡垒机表'
        verbose_name_plural = '堡垒机表'


class FortServerUser(models.Model):
    fort_user_status_ = (
        (0, '禁用'),
        (1, '正常')
    )
    fort_server = models.ForeignKey('FortServer', on_delete=models.CASCADE)
    fort_username = models.CharField(max_length=64, verbose_name='登录用户')
    fort_password = models.CharField(max_length=64, null=True, blank=True, verbose_name='登录密码')
    fort_user_status = models.SmallIntegerField(choices=fort_user_status_, default=1, verbose_name='用户状态')
    fort_vnc_port = models.CharField(max_length=5, blank=True, verbose_name='VNC连接端口', default='')
    fort_belong_user = models.ManyToManyField('users.UserProfile', blank=True, verbose_name='所属用户')
    fort_belong_group = models.ManyToManyField('auth.Group', blank=True, verbose_name='所属组')
    fort_black_commands = models.TextField(null=True, blank=True, verbose_name='禁用命令清单')
    fort_user_memo = models.TextField(null=True, blank=True, verbose_name='用户说明')

    class Meta:
        db_table = 'ops_fort_user'
        verbose_name = '堡垒机用户表'
        verbose_name_plural = '堡垒机用户表'
        unique_together = ('fort_server', 'fort_username')


class FortBlackCommand(models.Model):
    black_commands = models.TextField(verbose_name='默认禁用命令清单',
                                      default='/bin/rm, /sbin/reboot, /sbin/halt, /sbin/shutdown, /usr/bin/passwd, '
                                              '/bin/su, /sbin/init, /bin/chmod, /bin/chown, /usr/sbin/visudo')

    class Meta:
        db_table = 'ops_fort_black_command'
        verbose_name = '禁用命令清单表'
        verbose_name_plural = '禁用命令清单表'


class FortRecord(models.Model):
    record_modes = (
        ('ssh', 'ssh'),
        ('guacamole', 'guacamole')
    )

    login_user = models.ForeignKey('users.UserProfile', verbose_name='用户', on_delete=models.CASCADE)
    fort = models.CharField(max_length=32, verbose_name='登录主机及用户')
    remote_ip = models.GenericIPAddressField(verbose_name='远程地址')
    start_time = models.CharField(max_length=64, verbose_name='开始时间')
    login_status_time = models.CharField(max_length=16, verbose_name='登录时长')
    record_file = models.CharField(max_length=256, verbose_name='操作记录')
    record_mode = models.CharField(max_length=10, choices=record_modes, verbose_name='登录协议', default='ssh')
    record_cmds = models.TextField(verbose_name='命令记录', default='')

    class Meta:
        db_table = 'ops_fort_record'
        verbose_name = '操作记录表'
        verbose_name_plural = '操作记录表'
