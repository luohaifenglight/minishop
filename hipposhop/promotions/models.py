from django.db import models

# Create your models here.
from passport.models import PassportUser
from product.models import Product


class JieLong(models.Model):
    passport_user = models.ForeignKey(PassportUser,on_delete=models.CASCADE)
    title = models.CharField(verbose_name="商品标题", max_length=200)
    description = models.TextField(verbose_name="活动描述（推荐理由）", max_length=4000, null=True, blank=True, default="")
    image_url = models.ImageField("商品主图",max_length=1000, help_text="商品主图", default="", blank=True)
    begin_time = models.DateTimeField(verbose_name="活动开始时间", db_index=True)
    end_time = models.DateTimeField(verbose_name="活动结束时间", db_index=True)
    status = models.IntegerField(verbose_name="状态", choices=((0, "上架"), (1, "下架")), default=0, db_index=True)
    small_images = models.TextField(verbose_name="小图（空格分割）", max_length=4000, default="")
    commission_rate = models.DecimalField(verbose_name="佣金比率(%)", max_digits=6, decimal_places=2)
    wechat_no = models.CharField(verbose_name="微信号", max_length=50)
    is_logistics = models.IntegerField(verbose_name="是否需要物流配置", choices=((0, "否"), (1, "是")), default=0, db_index=True)
    browse_num = models.BigIntegerField(verbose_name="活动浏览量", default=0)
    display_order = models.IntegerField('显示排序', default=1, help_text="值越大越靠前")
    update_time = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    create_time = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')

    def __str__(self):
        return str(self.title)

    class Meta:
        verbose_name = "接龙表"
        verbose_name_plural = "接龙表"


class JielongProductRelation(models.Model):
    product = models.ForeignKey(Product,on_delete=models.CASCADE)
    jielong = models.ForeignKey(JieLong,on_delete=models.CASCADE)
    is_valid = models.IntegerField(verbose_name="是否有效", choices=((0, "是"), (1, "否")), default=0, db_index=True)
    update_time = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    create_time = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
