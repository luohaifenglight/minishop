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

    url(r'^v1/index$', views.get_customer_info_index),
    #我参与的接龙列表
    url(r'^v1/join_jielong$', views.get_my_join_jielong_list),
    url(r'^v1/my_fans', views.get_my_fans_list),
    url(r'^v1/my_follows', views.get_my_follows_list),
    #我发起的接龙列表
    url(r'^v1/spread_jielong', views.get_my_spread_jielong_list),
    url(r'^v1/share/join_user', views.get_share_join_user_list),
    url(r'^v1/share/browse_user', views.get_share_browse_user_list),
    url(r'^v1/browse/jielong', views.browse_jielong),
    url(r'^v1/spread/spread_tab', views.get_spread_tab),
    #推广人申请者列表
    url(r'^v1/spread/apply_user', views.get_spread_apply_user_list),
    #推广人列表
    url(r'^v1/spread/spread_user', views.get_spread_user_list),
    url(r'^v1/spread/apply_to_spreader', views.apply_to_spreader),
    url(r'^v1/spread/update_is_spreader', views.update_is_spreader),
    url(r'^v1/jielong/statistics$', views.get_jielong_statistics),
    url(r'^v1/jielong/share/statistics', views.get_jielong_share_statistics),
    url(r'^v1/update_my_fans', views.update_my_fans_after_order),
    url(r'^v1/jielong/statistics/order_list$', views.get_jielong_statistics_order_list),
    #我参与的接龙订单详情
    url(r'^v1/jielong/detail/my$', views.get_my_join_jielong_detail),
    # 导出所有订单并发送邮件
    url(r"^v1/export/send_email$", views.export_orders_send_to_inviter),
]