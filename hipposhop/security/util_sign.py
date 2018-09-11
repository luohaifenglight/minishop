# -*- coding: utf-8 -*-

import urlparse
import hashlib

from django.conf import settings
from security.models import AccessKeySecret
from utils.redis_common_util import RedisCommonUtil

class ApiSignatureUtil():
    '''

    1. 首先读取Redis缓存
    2. 缓存没有找到则读取数据库
    '''

    # 配置过期时间
    expire_seconds = 60*2
    redis_util = RedisCommonUtil()

    def __init__(self):
        pass

    @classmethod
    def _get_secret(cls, key):
        '''
        优先从redis缓存中读取，如果没有取到，再查找数据库，并缓存到redis\n
        :param key:
        :return:
        '''
        value = cls.redis_util.get_data(key)
        if not value:
            # redis没有找到对应的key, 查找数据库
            try:
                objs = AccessKeySecret.objects.get(key=key)
                value = objs.value
                # 把数据缓存到redis
                cls.redis_util.set_data(key, value, cls.expire_seconds)
                return value
            except AccessKeySecret.DoesNotExist:
                return None
        else:
            return value

    @classmethod
    def check_api_signature(cls, url_params):
        param_dict =  dict([(k, v[0]) for k, v in urlparse.parse_qs(url_params).items()])

        if param_dict.has_key("signature"):
            signature = param_dict['signature']
            param_dict.pop('signature')
        else:
            return False, "no signature in params"

        if param_dict.has_key("key"):
            key = param_dict['key']
        else:
            return False, "no key in params"

        secret = cls._get_secret(key)
        if not secret:
            return False, "Error, not find secret in AccessKeySecret"

        digest = sorted(param_dict.items(), key=lambda item: item[0])
        digest_str = ""
        for k, v in digest:
            digest_str += "%s%s" % (k ,v)
        digest_str = key + digest_str + secret
        md5 = hashlib.md5(digest_str.encode('utf-8')).hexdigest()
        md5sign = md5.upper()
        if signature == md5sign:
            return True, "check signature success."
        else:
            return False, "check signature failure"
