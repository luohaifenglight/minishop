from django.db import models

# Create your models here.

class Product(models.Model):
    title = models.CharField(verbose_name="商品标题", max_length=200)
    zk_final_price = models.DecimalField(verbose_name="在售价", max_digits=20, decimal_places=2)
    volume = models.BigIntegerField(verbose_name="销量")
    description = models.TextField(verbose_name="宝贝描述（推荐理由）", max_length=4000, null=True, blank=True, default="")
    sku_desc = models.CharField(verbose_name="规格描述", max_length=200)
    sku_num = models.BigIntegerField(verbose_name="商品库存量",default=0)
    max_buy_limit = models.BigIntegerField(verbose_name="商品购买数量限制", default=10)
    image_url = models.ImageField("商品主图",max_length=1000, help_text="商品主图", default="",blank=True)
    small_images = models.TextField(verbose_name="小图（空格分割）", max_length=4000, default="")
    video_url = models.CharField(verbose_name="视频地址", max_length=300)

    status = models.IntegerField(verbose_name="状态", choices=((0, "上架"), (1, "下架")), default=0, db_index=True)
    update_time = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    create_time = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')


    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "商品表"
        verbose_name_plural = "商品表"

