from django.db import models


class Project(models.Model):
    """项目表"""
    project_envs = (
        (0, '测试环境'),
        (1, '仿真环境'),
        (2, '生产环境')
    )
    project_models = (
        ('svn', 'svn'),
        ('git', 'git')
    )
    project_name = models.CharField(max_length=64, verbose_name='项目名称')
    project_env = models.SmallIntegerField(choices=project_envs, verbose_name='项目环境')
    project_web = models.CharField(max_length=64, blank=True, verbose_name='项目网址', default='')
    project_model = models.CharField(choices=project_models, max_length=3, verbose_name='仓库类型')
    project_repo = models.CharField(max_length=100, unique=True, verbose_name='项目仓库路径')
    project_dir = models.CharField(max_length=100, unique=True, verbose_name='项目代码目录')
    project_admin = models.ForeignKey('users.UserProfile', verbose_name='项目负责人', on_delete=models.PROTECT)
    project_memo = models.TextField(blank=True, verbose_name='项目描述', default='')

    class Meta:
        db_table = 'ops_project'
        verbose_name = '项目表'
        verbose_name_plural = '项目表'
        unique_together = ("project_env", "project_name")


class Service(models.Model):
    """服务类型表"""
    project = models.ForeignKey('Project', on_delete=models.CASCADE)
    service_name = models.CharField(max_length=32, verbose_name='服务名称', help_text='数据库、中间件等')
    service_asset = models.ForeignKey('assets.Assets', verbose_name='提供服务的机器', on_delete=models.CASCADE)
    service_memo = models.TextField(blank=True, verbose_name='服务描述', default='')

    class Meta:
        db_table = 'ops_service'
        verbose_name = '服务类型表'
        verbose_name_plural = '服务类型表'
        unique_together = ("project", "service_name")
