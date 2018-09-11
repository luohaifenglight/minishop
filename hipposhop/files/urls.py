from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^v1/upload', views.upload),
    url(r'^v1/share', views.share)
]