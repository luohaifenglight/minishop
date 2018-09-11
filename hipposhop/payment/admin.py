from django.contrib import admin

from . import models

# Register your models here.


@admin.register(models.WeChatRefund)
class WeChatRefundAdmin(admin.ModelAdmin):
    list_display = ("id", "order_id", "create_time",)
    search_fields = ("order_id",)


@admin.register(models.WeChatPay)
class WeChatPayAdmin(admin.ModelAdmin):
    list_display = ("id", "order_id", "create_time", "price","total_fee", "time_end",)
    search_fields = ("order_id", "price", "prepay_id",)