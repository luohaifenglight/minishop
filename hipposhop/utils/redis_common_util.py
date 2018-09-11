# -*- coding: utf-8 -*-


import logging
from django.conf import settings
import redis



class RedisCommonUtil():
    '''
    自定义Redis，用户缓存业务相关数据
    配置读取settings：
        HIPPO_REDIS_HOST
        HIPPO_REDIS_PASSWORD
        HIPPO_REDIS_PORT
        HIPPO_REDIS_DB
    '''
    logger = logging.getLogger('django.request')
    pool = redis.ConnectionPool(host=settings.HIPPO_REDIS_HOST,  password=settings.HIPPO_REDIS_PASSWORD,
                                port=settings.HIPPO_REDIS_PORT,
                                db=settings.HIPPO_REDIS_DB)
    client = redis.StrictRedis(connection_pool=pool)


    def __init__(cls):
        pass

    @classmethod
    def set_data(cls, key, value, expire=None):
        '''

        :param key:
        :param value:
        :param expire: 过期时间，单位秒
        :return:
        '''
        cls.client.set(key, value, ex=expire)

    @classmethod
    def get_data(cls, key):
        '''

        :param key:
        :return:
        '''
        value = cls.client.get(key)
        if value is None:
            return None
        return value

    @classmethod
    def del_data(cls, key):
        cls.client.delete(key)



