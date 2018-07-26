from django.db import models


class AnsibleModuleLog(models.Model):
    ans_user = models.ForeignKey('users.UserProfile', on_delete=models.PROTECT, verbose_name='操作用户')
    ans_remote_ip = models.GenericIPAddressField(verbose_name='操作用户IP')
    ans_module = models.CharField(max_length=100, verbose_name='模块名称')
    ans_args = models.CharField(max_length=500, blank=True, null=True, verbose_name='模块参数', default=None)
    ans_server = models.TextField(verbose_name='服务器')
    ans_result = models.TextField(verbose_name='执行结果')
    ans_datetime = models.DateTimeField(auto_now_add=True, verbose_name='执行时间')

    class Meta:
        db_table = 'ops_ansible_module_log'
        verbose_name = 'Ansible模块执行记录表'
        verbose_name_plural = 'Ansible模块执行记录表'


class AnsibleInventory(models.Model):
    ans_group_name = models.CharField(max_length=32, verbose_name='主机组名称')
    ans_group_hosts = models.ManyToManyField('assets.ServerAssets', verbose_name='组内主机')
    ans_group_vars = models.TextField(blank=True, null=True, verbose_name='主机组变量')
    ans_group_memo = models.TextField(blank=True, null=True, verbose_name='主机组描述')
    ans_group_adder = models.CharField(max_length=32, verbose_name='添加人')
    ans_group_datetime = models.DateTimeField(auto_now_add=True, verbose_name='添加时间')

    class Meta:
        db_table = 'ops_ansible_inventory'
        verbose_name = 'Ansible动态主机表'
        verbose_name_plural = 'Ansible动态主机表'
