from django.db import models


class DBConfig(models.Model):
    """数据库配置表"""
    db_server = models.OneToOneField('projs.Service', on_delete=models.CASCADE, verbose_name='数据库服务器')
    db_port = models.SmallIntegerField(verbose_name='数据库端口')
    db_name = models.CharField(max_length=64, verbose_name='数据库名称')
    db_user = models.CharField(max_length=64, verbose_name='数据库账号')
    db_password = models.CharField(max_length=64, verbose_name='数据库密码')
    db_group = models.ManyToManyField('auth.Group', verbose_name='使用组')
    db_memo = models.TextField(blank=True, verbose_name='备注', default='')

    class Meta:
        db_table = 'ops_db_config'
        verbose_name = '数据库配置表'
        verbose_name_plural = '数据库配置表'
        unique_together = ('db_server', 'db_name', 'db_port')


class DBLog(models.Model):
    """
    数据库操作记录表
    """
    db_config = models.ForeignKey('dbmanager.DBConfig', on_delete=models.CASCADE, verbose_name='登录数据库')
    db_login_user = models.ForeignKey('users.UserProfile', on_delete=models.CASCADE, verbose_name='执行用户')
    db_sql_content = models.TextField(verbose_name='SQL内容')
    db_sql_res = models.TextField(verbose_name='执行结果')
    db_sql_res_thead = models.CharField(max_length=256, blank=True, default='', verbose_name='查询结果的表头')
    db_run_datetime = models.DateTimeField(auto_now_add=True, verbose_name='执行时间')

    class Meta:
        db_table = 'ops_db_log'
        verbose_name = '数据库操作记录表'
        verbose_name_plural = '数据库操作记录表'
