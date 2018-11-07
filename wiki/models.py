from django.db import models


class Post(models.Model):
    title = models.CharField(max_length=70, verbose_name='文章标题', unique=True)
    html_content = models.TextField(verbose_name='HTML内容')
    md_content = models.TextField(verbose_name='markdown内容')
    created_time = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    modified_time = models.DateTimeField(auto_now_add=True, verbose_name='修改时间')
    author = models.ForeignKey('users.UserProfile', verbose_name='作者', on_delete=models.CASCADE)
    views = models.PositiveIntegerField(default=0)

    def increase_views(self):
        self.views += 1
        self.save(update_fields=['views'])

    class Meta:
        db_table = 'ops_wiki_post'
        verbose_name = 'wiki文章'
        verbose_name_plural = 'wiki文章'


class UploadImage(models.Model):
    image = models.ImageField(upload_to='wiki/images/%Y/%m/%d/', null=True, blank=True, verbose_name='图片地址')

    class Meta:
        db_table = 'ops_wiki_upload_image'
        verbose_name = 'wiki文章图片'
        verbose_name_plural = 'wiki文章图片'


class WikiFile(models.Model):
    upload_user = models.ForeignKey('users.UserProfile', verbose_name='上传人员', on_delete=models.CASCADE)
    wiki_file = models.FileField(upload_to='wiki/upload/%Y/%m/%d/', unique=True)
    upload_time = models.DateTimeField(auto_now_add=True, verbose_name='上传日期')

    class Meta:
        db_table = 'ops_wiki_file'
        verbose_name = 'wiki共享文件'
        verbose_name_plural = 'wiki共享文件'
