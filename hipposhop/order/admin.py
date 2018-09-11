from django.contrib import admin

# Register your models here.
from order.models import OrderUser, OrderDetail, Statement, WithdrawCash, FreezeAssert


@admin.register(OrderUser)
class OrderUserAdmin(admin.ModelAdmin):
    list_display = ("id", "trade_parent_id","pay_price","pay_time", "status","buyer_id","seller_id", "create_time",)
    search_fields = ("trade_parent_id","buyer_id","seller_id")
    list_filter = ("status",)


@admin.register(OrderDetail)
class OrderDetailAdmin(admin.ModelAdmin):
    list_display = ("id", "trade_parent_id","trade_id","num_iid", "item_title","item_num","price","create_time",)
    search_fields = ("trade_id","num_iid","item_title")


@admin.register(Statement)
class StatementAdmin(admin.ModelAdmin):
    list_display = ("user_id", "create_time", "balance",)
    search_fields = ("user_id", "balance",)


@admin.register(WithdrawCash)
class WithdrawCashAdmin(admin.ModelAdmin):
    list_display = ("create_time",)


@admin.register(FreezeAssert)
class FreezeAssertAdmin(admin.ModelAdmin):
    list_display = ("id", "relation_id", "create_time", "status")
    search_fields = ("relation_id", "user_id",)
    list_filter = ("status",)