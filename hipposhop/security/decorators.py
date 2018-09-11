# -*- coding: utf-8 -*-
import logging
from functools import wraps
import time
import urlparse

from django.contrib import auth
from django.http import HttpResponse, JsonResponse
from django.http import JsonResponse, HttpResponseNotFound
from django.utils.decorators import (
    available_attrs,
)

logger = logging.getLogger('django')


def api_sign_decorator(func):
    '''
    ＡPI签名校验的装饰器　＼ｎ
    :param func:
    :return:
    '''
    @wraps(func, assigned=available_attrs(func))
    def decorated_func(request, *args, **kwargs):
        full_path = request.get_full_path()
        query = urlparse.urlparse(full_path).query

        status, msg = ApiSignatureUtil.check_api_signature(query)
        if not status:
            print("check signature failure:%s" % msg)
            return JsonResponse({"status": 4, "err": "sign error"}, status=404)
        return func(request, *args, **kwargs)

    return decorated_func


def access_decorator(func):
    "cache for function result, which is immutable with fixed arguments"
    print("initial cache for %s" % func.__name__)
    cache = {}

    @wraps(func, assigned=available_attrs(func))
    def decorated_func(request, *args,**kwargs):
        # 函数的名称作为key
        key = func.__name__
        result = None
        #判断是否存在缓存
        if key in cache.keys():
            (result, updateTime) = cache[key]
            if time.time() - updateTime < 10:
                print("limit call 10s ", key)
                return HttpResponseNotFound("access control")
        else:
            print("no cache for ", key)

        #如果过期，或则没有缓存调用方法
        if result is None:
            result = func(request, *args, **kwargs)
            cache[key] = (result, time.time())

        return result

    return decorated_func



