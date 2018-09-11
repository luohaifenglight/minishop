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

    url(r'^v1/account_balance/list$', views.get_account_balance_list),
    #个人中心-我参与的接龙订单列表
    url(r'^v1/join_list$', views.get_join_order_list),
    #订单管理--卖家接龙订单列表
    url(r'^v1/jielong_list$', views.get_jielong_order_list),
    #订单详情
    url(r'^v1/detail$', views.get_order_detail),
    # 创建订单
    url(r'^v1/create$', views.order_create),
    url(r'^v1/cancel_order$', views.order_cancel),
    #申请提现
    url(r'^v1/apply_withdraw_cash', views.apply_withdraw_cash2),
    #提现记录列表
    url(r'^v1/withdraw_cash/list', views.withdraw_cash_list),
    url(r'^v1/update_commit', views.update_commit),
    #获取发货订单列表
    url(r'^v1/delivery/order$', views.get_delivery_order_list),
    # 获取发货订单列表
    url(r'^v1/copy_info$', views.get_order_copy_info),
    #获取退款订单数量
    url(r'^v1/refund/order/count$', views.get_refund_order_count),
    # 获取退款订单列表
    url(r'^v1/refund/order/list$', views.get_refund_order_list),
    # 申请退款
    url(r'^v1/refund/apply$', views.refund_apply),
    # 拒绝退款
    url(r'^v1/refund/refuse$', views.refund_refuse),
    # 同意退款
    url(r'^v1/refund/agree$', views.refund_agree),
]