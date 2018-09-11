from django.contrib import admin

# Register your models here.
from promotions.models import JieLong, JielongProductRelation

@admin.register(JieLong)
class JieLongAdmin(admin.ModelAdmin):
    list_display = ("id","title", "description","begin_time","end_time","status","commission_rate","wechat_no","browse_num")
    readonly_fields = ('create_time', 'update_time',)
    list_filter = ("status",)

@admin.register(JielongProductRelation)
class JielongProductRelationAdmin(admin.ModelAdmin):
    list_display = ("product","jielong","is_valid",)
    readonly_fields = ('create_time', 'update_time',)
    list_filter = ("is_valid",)
