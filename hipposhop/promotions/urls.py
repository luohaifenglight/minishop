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
    #发布/编辑接龙活动信息
    url(r'^v1/jielong/add$', views.add_jielong),
    #暂不使用
    url(r'^v1/jielong/edit$', views.add_jielong),
    #结束接龙活动
    url(r'^v1/jielong/cancel$', views.cancel_jielong),
    #编辑接龙时，查询当前接龙信息
    url(r'^v1/jielong/query$', views.query_jielong),
    #首页，当前登录人创建的接龙活动列表
    url(r'^v1/jielong/list$', views.get_jielong_list),
    #接龙活动详情页信息
    url(r'^v1/jielong/detail$', views.jielong_detail),
    #接龙详情页的当前接龙活动的下单记录
    url(r'^v1/jielong/order_list$', views.get_jielong_order_list),
    #当前接龙，我的下单接龙记录
    url(r'^v1/jielong/my_order_list$', views.get_my_jielong_order_list),
    url(r'^v1/test$', views.test),
]