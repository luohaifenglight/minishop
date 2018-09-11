from django.conf.urls import url

from passport import wechat_oauth_views
from . import views

urlpatterns = [
    # Examples:
    # url(r'^$', 'movie800.views.home', name='home'),
    # url(r'^movie800/', include('movie800.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:p
    # url(r'^admin/', include(admin.site.urls)),
    url(r'^v1/register$', views.register),
    url(r'^v1/login$', views.login),
    url(r'^v1/test$', views.test),
    url(r'^v1/update_wechat_user', views.update_user_info),
    url(r'^v1/wechat_auth', wechat_oauth_views.get_jscode2session),
    url(r'^v1/u_user_detail_info', views.update_user_detail_info),
]