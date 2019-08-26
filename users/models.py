from django.db import models
from django.contrib.auth.models import AbstractUser, Permission


class UserProfile(AbstractUser):
    login_status_ = (
        (0, '在线'),
        (1, '离线'),
        (2, '忙碌'),
        (3, '离开'),
    )
    mobile = models.CharField(max_length=11, null=True, blank=True, verbose_name='手机号码')
    image = models.ImageField(upload_to='images/%Y/%m/%d/', default='images/default.png', max_length=100)
    login_status = models.SmallIntegerField(choices=login_status_, default=1, verbose_name='登录状态')

    class Meta:
        db_table = 'ops_user'
        verbose_name = '用户表'
        verbose_name_plural = '用户表'


class UserPlan(models.Model):
    plan_status = (
        (0, '未完成'),
        (1, '已完成')
    )
    user = models.ForeignKey('UserProfile', related_name='self_user', on_delete=models.CASCADE, verbose_name='创建者')
    attention = models.ManyToManyField('UserProfile', related_name='attention_user', blank=True, verbose_name='关注者')
    title = models.CharField(max_length=32, verbose_name='计划标题')
    content = models.TextField(verbose_name='计划内容')
    status = models.PositiveSmallIntegerField(choices=plan_status, verbose_name='任务状态', default=0)
    start_time = models.DateTimeField(default='', verbose_name='开始时间')
    end_time = models.DateTimeField(default='', verbose_name='结束时间')
    add_time = models.DateTimeField(auto_now_add=True, verbose_name="添加时间")

    class Meta:
        db_table = 'ops_users_plan'
        verbose_name = '日程管理'
        verbose_name_plural = verbose_name
        unique_together = ('title', 'user')


class UserRole(models.Model):
    user_role_name = models.CharField(max_length=32, unique=True, verbose_name='角色名称')
    user_role_permissions = models.ManyToManyField('auth.Permission', verbose_name='角色拥有权限')
    group_role = models.ManyToManyField('auth.Group', verbose_name='组角色')
    u_role = models.ManyToManyField('UserProfile', verbose_name='用户角色')

    class Meta:
        db_table = 'ops_user_role'
        verbose_name = '角色管理'
        verbose_name_plural = verbose_name
