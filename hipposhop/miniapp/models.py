# Create your models here.
from django.db import models


# Create your models here.

class QRCodeURLParam(models.Model):
    query_param = models.CharField(verbose_name="url的参数", max_length=500, null=True, blank=True)
    url_path = models.CharField(verbose_name='小程序页面地址', max_length=255)
    md5_key = models.CharField(verbose_name='urlpath和query_param生成的md5', max_length=32, unique=True, db_index=True)
    qr_code_url = models.URLField(verbose_name="二维码地址", default="", blank=True)
    update_time = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    create_time = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')

    def __unicode__(self):
        return self.id

    class Meta:
        verbose_name = "二维码url参数表"
        verbose_name_plural = "二维码url参数表"


def get_qr_code_obj(qr_code_id):
    try:
        return QRCodeURLParam.objects.get(id=qr_code_id)
    except Exception as e:
        print(e)
        return None


def save_qr_code(url_path, query_string, md5_key):
    try:
        share_dict = {
            "md5_key": md5_key,
            "url_path": url_path,
            "query_param": query_string
        }

        return QRCodeURLParam.objects.update_or_create(md5_key=md5_key, defaults=share_dict)[0]
    except Exception as e:
        print(e)
        return None
