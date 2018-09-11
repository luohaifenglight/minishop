from django.contrib import admin

from hippoconfig.models import ErrorCode, ApplicationConfig, PlatformConfig, ServiceConfig



@admin.register(ErrorCode)
class ErrorCodeAdmin(admin.ModelAdmin):
    list_display = ("code", "msg", "type", "level")
    list_filter = ("type", "level",)
    search_fields = ("code",)
    readonly_fields = ('create_time', 'update_time',)
    ordering = ("code",)

    fieldsets = [
            (None,               {'fields': ['code', 'msg']}),
            ('information',     {'fields': ['type', 'level', 'memo']}),
        ]



@admin.register(ApplicationConfig)
class ApplicationConfigAdmin(admin.ModelAdmin):
    list_display = ("product_name", "product_code",)
    readonly_fields = ('create_time', 'update_time',)

@admin.register(PlatformConfig)
class PlatformConfigAdmin(admin.ModelAdmin):
    list_display = ("platform_name", "platform_code",)
    readonly_fields = ('create_time', 'update_time',)


@admin.register(ServiceConfig)
class ServiceConfigAdmin(admin.ModelAdmin):
    list_display = ("name", "key", "value", "app_config", "platform_config", "status")
    search_fields = ("name", "key")
    readonly_fields = ('create_time', 'update_time',)



