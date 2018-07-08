from django.db import models


class HostInfo(models.Model):
    TYPE_CHOICES = (
        (0, '物理机'),
        (1, '阿里云'),
        (2, '虚拟机'),
    )
    internal_ip = models.GenericIPAddressField(verbose_name="内网IP", unique=True)
    public_ip = models.GenericIPAddressField(verbose_name="外网IP", unique=True, null=True, blank=True)

    ssh_port = models.SmallIntegerField(null=True, verbose_name="ssh登录端口")
    ssh_user = models.CharField(max_length=32, null=True, verbose_name="ssh登录用户")
    ssh_passwd = models.CharField(max_length=64, null=True, verbose_name="ssh登录密码")

    system_ver = models.CharField(max_length=64, verbose_name="操作系统版本", default="")
    hostname = models.CharField(max_length=64, verbose_name="主机名", default="")
    host_type = models.SmallIntegerField(choices=TYPE_CHOICES, verbose_name='主机类型', default=0)
    sn = models.CharField(max_length=64, verbose_name="主机序号", default="")
    manufacturer = models.CharField(max_length=64, verbose_name='制造商')
    server_model = models.CharField(max_length=64, verbose_name='服务器型号')
    mac = models.CharField(max_length=32, verbose_name="MAC地址")
    total_mem = models.SmallIntegerField(verbose_name='内存容量，单位(M)')
    cpu_counts = models.SmallIntegerField(verbose_name='CPU逻辑数量')
    cpu_model = models.CharField(max_length=64, verbose_name='CPU型号')
    total_disk = models.CharField(max_length=16, verbose_name='硬盘容量')

    scan_datetime = models.DateTimeField(auto_now_add=True, verbose_name='扫描日期')

    class Meta:
        db_table = "ops_hostinfo"
        verbose_name = '扫描信息表'
        verbose_name_plural = verbose_name
        unique_together = (('hostname', 'mac'),)

    def __str__(self):
        return self.hostname
