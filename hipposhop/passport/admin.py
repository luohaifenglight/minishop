from django.contrib import admin

# Register your models here.
from passport.models import PassportUser, WechatUser

@admin.register(PassportUser)
class PassportUserAdmin(admin.ModelAdmin):
    list_display = ("id", "mobile","user_name","is_active", "create_time",)
    search_fields = ("mobile",)

@admin.register(WechatUser)
class WechatUserAdmin(admin.ModelAdmin):
    list_display = ("id", "openid","unionid","nickname", "create_time",)
    search_fields = ("unionid","openid",)