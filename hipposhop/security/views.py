# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import logging
from datetime import datetime

from django.views.decorators.cache import cache_control
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.shortcuts import render
from django.http import JsonResponse, HttpResponse, HttpResponseNotFound
from utils.serializer import DjangoJSONEncoder

from .models import AccessIp
from .decorators import access_decorator


@access_decorator
@require_http_methods(["GET"])
@csrf_exempt
#@cache_control(max_age=300)
def test(request):
    remote_ip = request.META['REMOTE_ADDR']
    try:
        ip_c = AccessIp.objects.get(ip=remote_ip)
        if ip_c:
            if (datetime.now() - ip_c.time).total_seconds() < 2:
                return HttpResponseNotFound("N分钟内只能访问一次")
            ip_c.time = datetime.now()
            ip_c.save()
    except Exception as e:
        new = AccessIp()
        new.ip = str(remote_ip)
        new.time = datetime.now()
        new.save()
        return HttpResponseNotFound("Forbidded")

    resp = {"status": 0, "results": {}}
    return JsonResponse(resp, encoder=DjangoJSONEncoder)


@access_decorator
def test_func(x):
    print('call test_func')

