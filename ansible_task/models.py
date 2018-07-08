from django.db import models


class AnsibleModuleLog(models.Model):
    ans_user = models.CharField(max_length=50, verbose_name='操作用户')
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
