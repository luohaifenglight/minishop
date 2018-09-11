"""hipposhop URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from django.conf.urls import url, include


admin.site.site_header = 'HippoShop(Alpha)'
admin.site.site_title = 'HippoShop'
admin.site.index_title = '首页'



urlpatterns = [
    path('hadmin/', admin.site.urls),

    url(r'^hsapi/product/', include('product.urls')),
    url(r'^hsapi/promotions/', include('promotions.urls')),
    url(r'^hsapi/customer/', include('customer.urls')),
    url(r'^hsapi/order/', include('order.urls')),
    url(r'^hsapi/payment/', include('payment.urls')),
    url(r'^hsapi/passport/', include('passport.urls')),
    url(r'^hsapi/file/', include('files.urls')),
    url(r'^hsapi/miniapp/', include('miniapp.urls'))
]
