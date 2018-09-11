from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^v1/qr_code$', views.get_qr_code),
    url(r'^v1/qr_param$', views.get_qr_param)
]