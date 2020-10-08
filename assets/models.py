from django.db import models


class Assets(models.Model):
    """总资产表"""
    asset_types = (
        ('server', '服务器'),
        ('network', '网络设备'),
        ('office', '办公设备'),
        ('security', '安全设备'),
        ('storage', '存储设备'),
        ('software', '软件资产'),
    )
    asset_status_ = (
        (0, '已上线'),
        (1, '已下线'),
        (2, '故障中'),
        (3, '未使用'),
    )
    asset_type = models.CharField(choices=asset_types, max_length=100, default='server', verbose_name='资产类型')
    asset_nu = models.CharField(max_length=100, unique=True, verbose_name='资产编号')
    asset_model = models.CharField(max_length=100, blank=True, null=True, verbose_name='资产型号')
    asset_provider = models.ForeignKey('AssetProvider', related_name='assets', null=True, blank=True,
                                       verbose_name='供应商', on_delete=models.PROTECT)
    asset_status = models.SmallIntegerField(choices=asset_status_, default=0, verbose_name='状态')
    asset_management_ip = models.GenericIPAddressField(blank=True, null=True, verbose_name='管理IP')
    asset_admin = models.ForeignKey('users.UserProfile', related_name='assets', verbose_name='资产管理员',
                                    on_delete=models.PROTECT)
    asset_idc = models.ForeignKey('IDC', related_name='assets', null=True, blank=True, verbose_name='所在机房',
                                  on_delete=models.PROTECT)
    asset_cabinet = models.ForeignKey('Cabinet', related_name='assets', null=True, blank=True, verbose_name='所在机柜',
                                      on_delete=models.PROTECT)

    asset_purchase_day = models.DateField(null=True, blank=True, verbose_name="购买日期")
    asset_expire_day = models.DateField(null=True, blank=True, verbose_name="过保日期")
    asset_price = models.CharField(max_length=100, null=True, blank=True, verbose_name="价格(万元)")

    asset_create_time = models.DateTimeField(auto_now_add=True)
    asset_update_time = models.DateTimeField(auto_now_add=True)
    asset_memo = models.TextField(null=True, blank=True, verbose_name='备注', help_text='配置说明或一些注意事项')

    class Meta:
        db_table = 'ops_assets'
        verbose_name = '总资产表'
        verbose_name_plural = '总资产表'


class ServerAssets(models.Model):
    """服务器设备"""
    server_types = (
        (0, '物理机'),
        (1, '虚拟机'),
        (2, '云主机'),
    )

    assets = models.OneToOneField('Assets', on_delete=models.CASCADE)
    server_type = models.SmallIntegerField(choices=server_types, default=0, verbose_name='服务器类型')

    username = models.CharField(max_length=100, blank=True, null=True, verbose_name='管理用户')
    password = models.CharField(max_length=100, blank=True, null=True, verbose_name='用户密码')
    port = models.DecimalField(max_digits=6, decimal_places=0, blank=True, null=True, default=22, verbose_name='SSH端口')

    hosted_on = models.ForeignKey('self', related_name='hosted_on_server',
                                  blank=True, null=True, verbose_name="宿主机", on_delete=models.PROTECT)  # 虚拟机专用字段

    hostname = models.CharField(max_length=100, blank=True, null=True, verbose_name='主机名称')
    cpu_model = models.CharField(max_length=100, blank=True, null=True, verbose_name='CPU型号')
    cpu_number = models.SmallIntegerField(blank=True, null=True, verbose_name='物理CPU个数')
    vcpu_number = models.SmallIntegerField(blank=True, null=True, verbose_name='逻辑CPU个数')
    disk_total = models.CharField(max_length=16, blank=True, null=True, verbose_name='磁盘空间')
    ram_total = models.SmallIntegerField(blank=True, null=True, verbose_name='内存容量')
    kernel = models.CharField(max_length=100, blank=True, null=True, verbose_name='内核版本')
    system = models.CharField(max_length=64, verbose_name='操作系统', default='linux')
    system_version = models.CharField(max_length=64, blank=True, verbose_name='系统版本', default='')

    host_vars = models.TextField(blank=True, null=True, verbose_name='主机变量')

    class Meta:
        db_table = 'ops_server_assets'
        verbose_name = '服务器资产表'
        verbose_name_plural = '服务器资产表'


class NetworkAssets(models.Model):
    """网络设备"""
    network_types = (
        (0, '路由器'),
        (1, '交换机'),
        (2, '负载均衡'),
        (3, 'wifi'),
        (4, 'VPN'),
        (5, '其它'),
    )
    assets = models.OneToOneField('Assets', on_delete=models.CASCADE)
    network_type = models.SmallIntegerField(choices=network_types, default=0, verbose_name='网络设备类型')

    class Meta:
        db_table = 'ops_network_assets'
        verbose_name = '网络资产表'
        verbose_name_plural = '网络资产表'


class OfficeAssets(models.Model):
    """办公设备"""
    office_types = (
        (0, 'PC机'),
        (1, '打印机'),
        (2, '扫描仪'),
        (3, '其它'),
    )
    assets = models.OneToOneField('Assets', on_delete=models.CASCADE)
    office_type = models.SmallIntegerField(choices=office_types, default=0, verbose_name='办公设备类型')

    class Meta:
        db_table = 'ops_office_assets'
        verbose_name = '办公资产表'
        verbose_name_plural = '办公资产表'


class SecurityAssets(models.Model):
    """安全设备"""
    security_types = (
        (0, '防火墙'),
        (1, '网关'),
        (2, '其它'),
    )
    assets = models.OneToOneField('Assets', on_delete=models.CASCADE)
    security_type = models.SmallIntegerField(choices=security_types, default=0, verbose_name='安全设备类型')

    class Meta:
        db_table = 'ops_security_assets'
        verbose_name = '安全资产表'
        verbose_name_plural = '安全资产表'


class StorageAssets(models.Model):
    """存储设备"""
    storage_types = (
        (0, '磁盘阵列'),
        (1, '网络存储器'),
        (2, '磁带库'),
        (3, '磁带机'),
        (4, '其它'),
    )
    assets = models.OneToOneField('Assets', on_delete=models.CASCADE)
    storage_type = models.SmallIntegerField(choices=storage_types, default=0, verbose_name='存储设备类型')

    class Meta:
        db_table = 'ops_storage_assets'
        verbose_name = '存储资产表'
        verbose_name_plural = '存储资产表'


class SoftwareAssets(models.Model):
    """只保存付费购买的软件"""
    software_types = (
        (0, '操作系统'),
        (1, '办公/开发软件'),
        (2, '业务软件'),
        (3, '其它'),
    )
    assets = models.OneToOneField('Assets', on_delete=models.CASCADE)
    software_type = models.SmallIntegerField(choices=software_types, default=0, verbose_name="软件类型")

    class Meta:
        db_table = 'ops_software_assets'
        verbose_name = '软件资产表'
        verbose_name_plural = '软件资产表'


class DiskAssets(models.Model):
    asset = models.ForeignKey('Assets', related_name='disk_assets', on_delete=models.CASCADE)
    disk_volume = models.CharField(max_length=100, blank=True, null=True, verbose_name='硬盘容量')
    disk_status = models.CharField(max_length=100, blank=True, null=True, verbose_name='硬盘状态')
    disk_model = models.CharField(max_length=100, blank=True, null=True, verbose_name='硬盘型号')
    disk_brand = models.CharField(max_length=100, blank=True, null=True, verbose_name='硬盘生产商')
    disk_serial = models.CharField(max_length=100, blank=True, null=True, verbose_name='硬盘序列号')
    disk_slot = models.SmallIntegerField(blank=True, null=True, verbose_name='硬盘插槽')

    class Meta:
        db_table = 'ops_disk_assets'
        unique_together = ("asset", "disk_slot")
        verbose_name = '磁盘资产表'
        verbose_name_plural = '磁盘资产表'


class RamAssets(models.Model):
    asset = models.ForeignKey('Assets', related_name='ram_assets', on_delete=models.CASCADE)
    ram_serial = models.CharField(max_length=100, blank=True, null=True, verbose_name='内存序列号')
    ram_volume = models.CharField(max_length=100, blank=True, null=True, verbose_name='内存容量')
    ram_brand = models.CharField(max_length=100, blank=True, null=True, verbose_name='内存生产商')
    ram_slot = models.SmallIntegerField(blank=True, null=True, verbose_name='内存插槽')

    class Meta:
        db_table = 'ops_ram_assets'
        unique_together = ("asset", "ram_slot")
        verbose_name = '内存资产表'
        verbose_name_plural = '内存资产表'


class NetworkCardAssets(models.Model):
    asset = models.ForeignKey('Assets', related_name='network_card_assets', on_delete=models.CASCADE)
    network_card_name = models.CharField(max_length=20, blank=True, null=True, verbose_name='网卡名称')
    network_card_mac = models.CharField(max_length=64, blank=True, null=True, verbose_name='MAC地址')
    network_card_ip = models.CharField(max_length=16, blank=True, null=True, verbose_name='IP地址')
    network_card_model = models.CharField(max_length=50, blank=True, null=True, verbose_name='网卡类型')
    network_card_mtu = models.CharField(max_length=50, blank=True, null=True, verbose_name='MTU')
    network_card_status = models.SmallIntegerField(blank=True, null=True, verbose_name='网卡状态')

    class Meta:
        db_table = 'ops_network_card_assets'
        unique_together = ("asset", "network_card_mac")
        verbose_name = '服务器网卡资产表'
        verbose_name_plural = '服务器网卡资产表'


class AssetProvider(models.Model):
    """供应商"""
    asset_provider_name = models.CharField(max_length=64, unique=True, verbose_name='供应商名称')
    asset_provider_contact = models.CharField(max_length=32, blank=True, null=True, verbose_name='技术支持人员')
    asset_provider_telephone = models.CharField(max_length=11, blank=True, null=True, verbose_name='支持电话')
    asset_provider_memo = models.CharField(max_length=128, blank=True, null=True, verbose_name='备注')

    class Meta:
        db_table = 'ops_asset_provider'
        verbose_name = '供应商表'
        verbose_name_plural = '供应商表'


class IDC(models.Model):
    """机房表"""
    idc_name = models.CharField(max_length=64, unique=True, verbose_name='机房名称')
    idc_address = models.CharField(max_length=100, unique=True, verbose_name='机房地址')
    idc_contact = models.CharField(max_length=32, verbose_name='机房联系人')
    idc_telephone = models.CharField(max_length=11, blank=True, null=True, verbose_name='支持电话')
    idc_memo = models.CharField(max_length=100, blank=True, null=True, verbose_name='备注')

    class Meta:
        db_table = 'ops_idc'
        verbose_name = '机房表'
        verbose_name_plural = '机房表'


class Cabinet(models.Model):
    """机柜表"""
    idc = models.ForeignKey('IDC', related_name='cabinet', on_delete=models.CASCADE)
    cabinet_name = models.CharField(max_length=64, unique=True, verbose_name='机柜名称')
    cabinet_memo = models.CharField(max_length=100, blank=True, null=True, verbose_name='备注')

    class Meta:
        db_table = 'ops_cabinet'
        verbose_name = '机柜表'
        verbose_name_plural = '机柜表'


class AdminRecord(models.Model):
    record_modes = (
        ('ssh', 'ssh'),
        ('guacamole', 'guacamole')
    )

    admin_login_user = models.ForeignKey('users.UserProfile', verbose_name='用户', on_delete=models.CASCADE)
    admin_server = models.CharField(max_length=32, verbose_name='登录主机')
    admin_remote_ip = models.GenericIPAddressField(verbose_name='远程地址')
    admin_start_time = models.CharField(max_length=64, verbose_name='开始时间')
    admin_login_status_time = models.CharField(max_length=16, verbose_name='登录时长')
    admin_record_file = models.CharField(max_length=256, verbose_name='操作记录')
    admin_record_mode = models.CharField(max_length=10, choices=record_modes, verbose_name='登录协议', default='ssh')
    admin_record_cmds = models.TextField(verbose_name='命令记录', default='')

    class Meta:
        db_table = 'ops_admin_record'
        verbose_name = '登录管理用户记录表'
        verbose_name_plural = '登录管理用户记录表'


class ZabbixAlert(models.Model):
    alert_num = models.SmallIntegerField(verbose_name='告警数量')
    alert_date = models.DateField(auto_now_add=True, verbose_name='告警日期')

    class Meta:
        db_table = 'ops_zabbix_alert'
        verbose_name = '告警记录表'
        verbose_name_plural = '告警记录表'


class WebSite(models.Model):
    web_name = models.CharField(max_length=32, verbose_name='网站名称')
    web_address = models.URLField(verbose_name='网站地址')
    web_des = models.CharField(max_length=32, verbose_name='网站描述')

    class Meta:
        db_table = 'ops_website'
        verbose_name = '常用网站表'
        verbose_name_plural = '常用网站表'


class PullAssetConf(models.Model):
    cloud_names = (
        ('ali', '阿里云'),
    )
    conf_name = models.CharField(max_length=16, verbose_name='配置名称')
    cloud_name = models.CharField(max_length=16, choices=cloud_names, verbose_name='云厂商', default='ali')
    cloud_region = models.CharField(max_length=64, verbose_name='区域')
    access_id = models.CharField(max_length=128, verbose_name='AccessID')
    access_key = models.CharField(max_length=128, verbose_name='AccessKey')
    conf_memo = models.TextField(verbose_name='配置描述', default='', blank=True)
    belong_user = models.ForeignKey('users.UserProfile', on_delete=models.CASCADE, verbose_name='所属用户')
    server_user = models.CharField(max_length=16, verbose_name='系统管理用户', default='')
    server_user_password = models.CharField(max_length=128, verbose_name='系统管理用户密码', default='')
    server_port = models.SmallIntegerField(verbose_name='管理端口', default=22)

    class Meta:
        db_table = 'ops_pull_conf'
        verbose_name = '同步云主机配置表'
        verbose_name_plural = '同步云主机配置表'
