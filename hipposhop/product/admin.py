from django.contrib import admin

# Register your models here.
from product.models import Product

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("id","title", "zk_final_price","sku_desc","sku_num","max_buy_limit")
    readonly_fields = ('create_time', 'update_time',)