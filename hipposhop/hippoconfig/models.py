from django.db import models

# Create your models here.

class ErrorCode(models.Model):
    '''
    Kangaroo系统错误代码表:\n
    1. 代码长度5位 \n
    2. 1xxxx:系统错误\n
       2xxxx:用户账号类错误\n
       3xxxx:商品类错误\n
       5xxxx:外部系统错误\n
       9xxxxx:其它\n
    '''
    ERROR_TYPES = (
        (10, '10-系统错误'),
        (20, '20-用户账号类错误'),
        (30, '30-商品类错误'),
        (40, '40-微信系统错误'),
        (50, '50-外部系统错误'),
        (90, '90-其它'),
    )
    ERROR_LEVEL = (
        (10, '调试-DEBUG'),
        (20, '通知-INFO'),
        (30, '警告-WARNING'),
        (40, '错误-ERROR'),
        (50, '致命错误-CRITICAL'),
    )

    code = models.IntegerField(verbose_name='错误代码', unique=True,
                               help_text="前两位标识错误类型，后三位标识具体的错误码，1x:系统错误, 2x:用户账号错误,3x:商品类错误, 4x:淘宝错误，5x:外部系统错误,9x:其它")
    msg = models.CharField(verbose_name="错误信息", max_length=512, help_text="错误信息")
    type = models.IntegerField(verbose_name='错误类别', choices=ERROR_TYPES, help_text="错误代码的前两位和错误类别代码要一致")
    level = models.IntegerField(verbose_name='错误级别', choices=ERROR_LEVEL, help_text="错误级别")
    memo = models.TextField(verbose_name="备注", max_length=1000, default="")
    create_time = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    update_time = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    def __str__(self):
        return str(self.code)

    class Meta:
        verbose_name = "错误代码表"
        verbose_name_plural = "错误代码表(规范)"


class ApplicationConfig(models.Model):
    product_name = models.CharField(verbose_name='应用名称', max_length=256)
    product_code = models.CharField(verbose_name='应用代码', max_length=256, db_index=True, help_text='全部小写字母，可以使用下划线')
    update_time = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    create_time = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')

    def __str__(self):
        return self.product_name

    class Meta:
        verbose_name = "产品配置"
        verbose_name_plural = "产品配置"


class PlatformConfig(models.Model):
    platform_name = models.CharField(verbose_name='平台名称', max_length=256)
    platform_code = models.CharField(verbose_name='平台代码', max_length=256, db_index=True, help_text='全部小写字母，可以使用下划线')
    update_time = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    create_time = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')

    def __str__(self):
        return self.platform_name

    class Meta:
        verbose_name = "平台配置"
        verbose_name_plural = "平台配置"


class ServiceConfig(models.Model):
    name = models.CharField('配置名称', max_length=256)
    key = models.CharField('Key', max_length=128, db_index=True)
    value = models.TextField(verbose_name="Value")
    status = models.IntegerField(verbose_name="状态", choices=((0, "Enabled"), (1, "Disabled"), (2, "Discard")),
                                 default=0)
    description = models.CharField('备注', max_length=256)
    app_config = models.ForeignKey(ApplicationConfig, on_delete=models.CASCADE)
    platform_config = models.ForeignKey(PlatformConfig, on_delete=models.CASCADE)
    update_time = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    create_time = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')

    def __str__(self):
        return self.key

    class Meta:
        verbose_name = "服务配置"
        verbose_name_plural = "服务配置管理"



