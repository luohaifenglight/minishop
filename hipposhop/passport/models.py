from django.db import models


# Create your models here.

class PassportUser(models.Model):
    user_name = models.CharField(verbose_name="用户名", max_length=150, null=True, blank=True)
    mobile = models.CharField(verbose_name='手机号', max_length=50, null=True, blank=True)
    password = models.CharField(verbose_name='密码', max_length=128, null=True)
    email = models.EmailField(verbose_name='邮箱', blank=True, null=True)
    avatar_url = models.URLField(verbose_name="头像", default="", blank=True)
    is_active = models.BooleanField(verbose_name='是否激活', default=True, )
    update_time = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    create_time = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    last_login = models.DateTimeField(verbose_name='最后登陆时间', blank=True, null=True)

    def __str__(self):
        return str(self.id)

    class Meta:
        verbose_name = "基础用户"
        verbose_name_plural = "基础用户"


class WechatUser(models.Model):
    passport_user = models.OneToOneField(PassportUser, on_delete=models.CASCADE, db_index=True)
    unionid = models.CharField(verbose_name='unionid', max_length=64, null=True, blank=True)
    openid = models.CharField(verbose_name='openid', max_length=64)
    session_key = models.CharField(verbose_name='微信session_key', max_length=256, null=True, blank=True)
    nickname = models.CharField(verbose_name='昵称', max_length=128, null=True)
    avatar_url = models.URLField(verbose_name="头像", default="", blank=True)
    refresh_token = models.CharField(verbose_name='refresh_token, 30天有效期', max_length=256, null=False)
    update_time = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    create_time = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')

    def __str__(self):
        return str(self.unionid)

    class Meta:
        verbose_name = "微信用户"
        verbose_name_plural = "微信用户"

class Session(models.Model):
    passport_user = models.OneToOneField(PassportUser,on_delete=models.CASCADE, db_index=True)
    session_key = models.CharField(verbose_name='session key', max_length=128, unique=True)
    session_data = models.TextField(verbose_name='session data')
    expire_date = models.DateTimeField(verbose_name='expire date', db_index=True)
