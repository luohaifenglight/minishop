# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import json
import logging
from urllib.parse import urlencode

import requests
# app 用
from django.conf import settings

from utils.redis_common_util import RedisCommonUtil

logger = logging.getLogger("django.request")


def get_token_cache_key(grant_type="client_credential"):
    return "%s:token" % grant_type


def get_access_token(app_id=settings.MINI_APPID, secret=settings.MINI_SECRET, grant_type="client_credential"):
    """
    获取微信access_token, token有效期为7200秒，不能频繁调用该接口， 需要做缓存
    :param app_id:
    :param secret:
    :param grant_type:
    :return:
    """
    cache_key = get_token_cache_key(grant_type)
    access_token = RedisCommonUtil.get_data(cache_key)
    if access_token:
        return access_token

    params = {
        'appid': app_id,
        'secret': secret,
        'grant_type': grant_type
    }
    try:
        data = urlencode(params)
        first = 'https://api.weixin.qq.com/cgi-bin/token?%s'
        result_url = first % data
        open_data = requests.get(result_url)
        result_data = json.loads(open_data.text)
        access_token = result_data["access_token"]
        expires_in = result_data["expires_in"]
        cache_time = expires_in - 30
        if cache_time > 5:
            RedisCommonUtil.set_data(cache_key, access_token, cache_time)
        return access_token
    except Exception as e:
        print(e)
        return None


def get_qr_code_image(access_token, scene, page):
    """
    参考：
    https://developers.weixin.qq.com/miniprogram/dev/api/qrcode.html
    :param access_token:
    :param scene:
    :param page:
    :return:
    """
    params = {
        'access_token': access_token
    }
    post_param = {
        'scene': str(scene),
        'page': page,
        'width': 300
    }

    try:
        data = urlencode(params)
        first = 'https://api.weixin.qq.com/wxa/getwxacodeunlimit?%s'
        result_url = first % data
        # resp = requests.post(result_url, None, post_param)
        resp = requests.post(result_url, data=json.dumps(post_param))
        logger.info("get_qr_code_image result_url:%s; result:%s" % (result_url, resp))
        return resp
    except Exception as e:
        print(e)
        return None
