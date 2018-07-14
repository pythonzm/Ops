from django.db import models


class Assets(models.Model):
    """总资产表"""
    asset_type_choices = (
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
    asset_type = models.CharField(choices=asset_type_choices, max_length=100, default='server', verbose_name='资产类型')
    asset_nu = models.CharField(max_length=100, verbose_name='资产编号', unique=True)
    asset_model = models.CharField(max_length=100, blank=True, null=True, verbose_name='资产型号')
    asset_provider = models.ForeignKey('AssetProvider', null=True, blank=True, verbose_name='供应商',
                                       on_delete=models.PROTECT)
    asset_status = models.SmallIntegerField(choices=asset_status_, blank=True, null=True, verbose_name='状态')
    asset_management_ip = models.GenericIPAddressField(blank=True, null=True, verbose_name='管理IP')
    asset_admin = models.ForeignKey('users.UserProfile', verbose_name='资产管理员', on_delete=models.PROTECT)
    asset_project = models.ManyToManyField('Project', verbose_name='所属项目', blank=True)
    asset_idc = models.ForeignKey('IDC', null=True, blank=True, verbose_name='所在机房', on_delete=models.PROTECT)
    asset_cabinets = models.ForeignKey('Cabinets', null=True, blank=True, verbose_name='所在机柜', on_delete=models.PROTECT)

    asset_purchase_day = models.DateField(null=True, blank=True, verbose_name="购买日期")
    asset_expire_day = models.DateField(null=True, blank=True, verbose_name="过保日期")
    asset_price = models.FloatField(null=True, blank=True, verbose_name="价格")

    asset_create_time = models.DateTimeField(auto_now_add=True)
    asset_update_time = models.DateTimeField(auto_now_add=True)
    asset_memo = models.TextField(null=True, blank=True, verbose_name='备注', help_text='配置说明或一些注意事项')

    class Meta:
        db_table = 'ops_assets'
        verbose_name = '总资产表'
        verbose_name_plural = '总资产表'
        ordering = ['-asset_create_time']


class ServerAssets(models.Model):
    """服务器设备"""
    server_types = (
        (0, '物理机'),
        (1, '虚拟机'),
        (2, '云主机'),
    )
    auth_types = (
        (0, '密钥认证'),
        (1, '账户密码'),
    )
    asset = models.OneToOneField('Assets', on_delete=models.PROTECT)
    server_type = models.SmallIntegerField(choices=server_types, default=0, verbose_name='服务器类型')

    server_ip = models.GenericIPAddressField(verbose_name='IP地址', unique=True)

    # 如果采用用户名密码认证方式，账户、密码、端口必填，采用密钥认证可不用填写
    username = models.CharField(max_length=100, blank=True, null=True, verbose_name='用户名称')
    auth_type = models.SmallIntegerField(choices=auth_types, default=0, verbose_name='认证方式')
    password = models.CharField(max_length=100, blank=True, null=True, verbose_name='用户密码')
    port = models.DecimalField(max_digits=6, decimal_places=0, blank=True, null=True, verbose_name='SSH端口')

    hosted_on = models.ForeignKey('self', related_name='hosted_on_server',
                                  blank=True, null=True, verbose_name="宿主机", on_delete=models.PROTECT)  # 虚拟机专用字段

    hostname = models.CharField(max_length=100, blank=True, null=True, verbose_name='主机名称')
    cpu_model = models.CharField(max_length=100, blank=True, null=True, verbose_name='CPU型号')
    cpu_number = models.SmallIntegerField(blank=True, null=True, verbose_name='物理CPU个数')
    vcpu_number = models.SmallIntegerField(blank=True, null=True, verbose_name='逻辑CPU个数')
    disk_total = models.IntegerField(blank=True, null=True, verbose_name='磁盘空间')
    ram_total = models.SmallIntegerField(blank=True, null=True, verbose_name='内存容量')
    kernel = models.CharField(max_length=100, blank=True, null=True, verbose_name='内核版本')
    system = models.CharField(max_length=100, blank=True, null=True, verbose_name='操作系统')

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
    asset = models.OneToOneField('Assets', on_delete=models.PROTECT)
    network_type = models.SmallIntegerField(choices=network_types, default=0, verbose_name='网络设备类型')

    port_number = models.SmallIntegerField(blank=True, null=True, verbose_name='端口个数')
    firmware = models.CharField(max_length=100, blank=True, null=True, verbose_name='固件版本')

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
    asset = models.OneToOneField('Assets', on_delete=models.PROTECT)
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
    asset = models.OneToOneField('Assets', on_delete=models.PROTECT)
    security_type = models.SmallIntegerField(choices=security_types, default=0, verbose_name='安全设备类型')

    class Meta:
        db_table = 'ops_security_assets'
        verbose_name = '安全资产表'
        verbose_name_plural = '安全资产表'


class StorageAssets(models.Model):
    """存储设备"""
    storage_types = (
        (0, '防火墙'),
        (1, '网关'),
        (2, '其它'),
    )
    asset = models.OneToOneField('Assets', on_delete=models.PROTECT)
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
    )
    asset = models.OneToOneField('Assets', on_delete=models.PROTECT)
    software_type = models.SmallIntegerField(choices=software_types, default=0, verbose_name="软件类型")

    class Meta:
        db_table = 'ops_software_assets'
        verbose_name = '软件资产表'
        verbose_name_plural = '软件资产表'


class DiskAssets(models.Model):
    asset = models.ForeignKey('ServerAssets', on_delete=models.PROTECT)
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
    asset = models.ForeignKey('ServerAssets', on_delete=models.PROTECT)
    ram_model = models.CharField(max_length=100, blank=True, null=True, verbose_name='内存型号')
    ram_volume = models.CharField(max_length=100, blank=True, null=True, verbose_name='内存容量')
    ram_brand = models.CharField(max_length=100, blank=True, null=True, verbose_name='内存生产商')
    ram_slot = models.SmallIntegerField(blank=True, null=True, verbose_name='内存插槽')
    ram_status = models.CharField(max_length=100, blank=True, null=True, verbose_name='内存状态')

    class Meta:
        db_table = 'ops_ram_assets'
        unique_together = ("asset", "ram_slot")
        verbose_name = '内存资产表'
        verbose_name_plural = '内存资产表'


class NetworkCardAssets(models.Model):
    asset = models.ForeignKey('ServerAssets', on_delete=models.PROTECT)
    network_card_name = models.CharField(max_length=20, blank=True, null=True, verbose_name='网卡名称')
    network_card_mac = models.CharField(max_length=64, blank=True, null=True, verbose_name='MAC地址')
    network_card_ip = models.GenericIPAddressField(blank=True, null=True, verbose_name='IP地址')
    network_card_model = models.CharField(max_length=50, blank=True, null=True, verbose_name='网卡类型')
    network_card_mtu = models.CharField(max_length=50, blank=True, null=True, verbose_name='MTU')
    network_card_status = models.SmallIntegerField(blank=True, null=True, verbose_name='网卡状态')

    class Meta:
        db_table = 'ops_network_card_assets'
        unique_together = ("asset", "network_card_mac")
        verbose_name = '服务器网卡资产表'
        verbose_name_plural = '服务器网卡资产表'


class Project(models.Model):
    """项目表"""
    parent_project = models.ForeignKey('self', blank=True, null=True, related_name='parent_level',
                                       on_delete=models.PROTECT)
    project_name = models.CharField(max_length=64, unique=True, verbose_name='项目名称')
    project_memo = models.CharField(max_length=100, blank=True, null=True, verbose_name='基本描述')

    class Meta:
        db_table = 'ops_project'
        verbose_name = '项目表'
        verbose_name_plural = '项目表'


class Business(models.Model):
    """业务表"""
    project_name = models.ForeignKey('Project', on_delete=models.PROTECT)
    business_name = models.CharField(max_length=32, verbose_name='业务名称', help_text='数据库、中间件等')
    business_memo = models.CharField(max_length=100, blank=True, null=True, verbose_name='基本描述')

    class Meta:
        db_table = 'ops_business'
        verbose_name = '业务表'
        verbose_name_plural = '业务表'


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
    """机房"""
    idc_name = models.CharField(max_length=64, unique=True, verbose_name='机房名称')
    idc_address = models.CharField(max_length=100, unique=True, verbose_name='机房地址')
    idc_contact = models.CharField(max_length=32, unique=True, verbose_name='机房联系人')
    idc_telephone = models.CharField(max_length=11, blank=True, null=True, verbose_name='支持电话')
    idc_memo = models.CharField(max_length=100, blank=True, null=True, verbose_name='备注')

    class Meta:
        db_table = 'ops_idc'
        verbose_name = '机房表'
        verbose_name_plural = '机房表'


class Cabinets(models.Model):
    """机柜表"""
    idc = models.ForeignKey('IDC', on_delete=models.PROTECT)
    cabinets_name = models.CharField(max_length=64, unique=True, verbose_name='机柜名称')
    cabinets_memo = models.CharField(max_length=100, blank=True, null=True, verbose_name='备注')

    class Meta:
        db_table = 'ops_cabinets'
        verbose_name = '机柜表'
        verbose_name_plural = '机柜表'
