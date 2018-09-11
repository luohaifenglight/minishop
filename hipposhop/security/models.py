# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models

# Create your models here.


class AccessKeySecret(models.Model):
    access_name = models.CharField(verbose_name='名称',max_length=50, unique=True)
    key = models.CharField(verbose_name='Key',max_length=50, unique=True)
    secret = models.CharField(verbose_name='Secret',max_length=500)
    comments = models.TextField(verbose_name="备注", max_length=500,  null=True, blank=True, default="")
    update_time = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    create_time = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    is_active = models.BooleanField('是否有效', default=True)
    start_time =  models.DateTimeField(verbose_name='开始时间')
    end_time =  models.DateTimeField(verbose_name='结束时间')

    class Meta:
        verbose_name = u'AccessKey管理'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.access_name


class AccessIp(models.Model):
    ip = models.CharField(max_length=20, unique=True)
    time = models.DateTimeField()

    class Meta:
        verbose_name = u'访问时间'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.ip