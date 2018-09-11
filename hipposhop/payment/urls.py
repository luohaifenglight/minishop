from django.conf.urls import url

from . import views

urlpatterns = [
    # Examples:
    # url(r'^$', 'movie800.views.home', name='home'),
    # url(r'^movie800/', include('movie800.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:p
    # url(r'^admin/', include(admin.site.urls)),
    url(r'^v1/order/pay$', views.order_pay),
    url(r'^v1/get_order', views.get_order),
    url(r'^v1/get_refund_order', views.get_refund_order),
    # url(r'^v1/test_hack', views.test_hack)
]
