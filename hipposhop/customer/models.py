from django.db import models

# Create your models here.
from passport.models import PassportUser
from promotions.models import JieLong

class ShareUserRelation(models.Model):
    browse_user = models.ForeignKey(PassportUser,on_delete=models.CASCADE,verbose_name="浏览用户")
    share_user_id = models.BigIntegerField(verbose_name="分享用户id")
    share_user_role = models.IntegerField(verbose_name="分享用户身份", choices=((0, "普通用户"), (1, "推广人")), default=0)
    jielong = models.ForeignKey(JieLong,on_delete=models.CASCADE,verbose_name="接龙活动")
    browse_num = models.BigIntegerField(verbose_name="活动浏览量", default=0)
    update_time = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    create_time = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')

    def __unicode__(self):
        return self.id

    class Meta:
        verbose_name = "分享用户关系表"
        verbose_name_plural = "分享用户关系表"


class Address(models.Model):
    user_id = models.BigIntegerField(verbose_name="用户")
    mobile = models.CharField(verbose_name="收货人电话", max_length=150)
    postal_code = models.CharField(verbose_name="邮编", max_length=150)
    name = models.CharField(verbose_name="收货人姓名", max_length=150)
    province = models.CharField(verbose_name="国际收货一级地址", max_length=150)
    country = models.CharField(verbose_name="国际收货二级地址家", max_length=150)
    city = models.CharField(verbose_name="国际收货三级地址", max_length=150)
    address_detail = models.CharField(verbose_name="收货地址详情", max_length=500)
    national_code = models.CharField(verbose_name="国际编码 ", max_length=500)
    update_time = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    create_time = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')

    def __str__(self):
        return self.address_detail

    class Meta:
        verbose_name = "收货地址"
        verbose_name_plural = "收货地址"

class JieLongUserRelation(models.Model):
    passport_user = models.ForeignKey(PassportUser,on_delete=models.CASCADE,verbose_name="参与用户")
    jielong = models.ForeignKey(JieLong,on_delete=models.CASCADE,verbose_name="接龙活动")
    is_attention = models.IntegerField(verbose_name="是否关注", choices=((0, "关注"), (1, "未关注")), default=0, db_index=True)
    update_time = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    create_time = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')

    def __unicode__(self):
        return self.id

    class Meta:
        verbose_name = "接龙参与用户关系表"
        verbose_name_plural = "接龙参与用户关系表"

class JieLongSpreadUserRelation(models.Model):
    passport_user = models.ForeignKey(PassportUser,on_delete=models.CASCADE,verbose_name="参与用户")
    invite_sponsor_id = models.BigIntegerField(verbose_name="邀请推广用户id")
    status = models.IntegerField(verbose_name="推广人状态", choices=((0, "申请中"), (1, "同意申请"),(2, "拒绝申请"),(3, "取消推广人")), default=0, db_index=True)
    apply_reason = models.CharField(verbose_name="申请理由 ", max_length=500,null=True,blank=True,default="")
    wechat_no = models.CharField(verbose_name="微信号 ", max_length=50, null=True, blank=True, default="")
    update_time = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    create_time = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')

    def __unicode__(self):
        return self.id

    class Meta:
        verbose_name = "推广人用户关系表"
        verbose_name_plural = "推广人用户关系表"
