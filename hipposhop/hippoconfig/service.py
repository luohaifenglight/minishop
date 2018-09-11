# -*- coding: utf-8 -*-


from utils.redis_common_util import RedisCommonUtil
from hippoconfig.models import ServiceConfig


class ConfigService(object):
    '''
    读取Appconfig配置新的的工具类\n
    1. 首先读取Redis缓存
    2. 缓存没有找到则读取数据库
    '''

    # 配置过期时间
    expire_seconds = 60*2
    redis_util = RedisCommonUtil()

    def __init__(self):
        pass

    @classmethod
    def _get_config(cls, key):
        '''
        从appconfig的ServiceConfig表中读取配置数据\n
        优先从redis缓存中读取，如果没有取到，再查找数据库，并缓存到redis\n

        :param key:
        :return:
        '''
        value = cls.redis_util.get_data(key)
        if not value:
            # redis没有找到对应的key, 查找数据库
            try:
                config = ServiceConfig.objects.get(key=key)
                value = config.value
                # 把数据缓存到redis
                cls.redis_util.set_data(key, value, cls.expire_seconds)
                return value
            except ServiceConfig.DoesNotExist:
                return None
        else:
            return value

    @classmethod
    def get_config_str(cls, key):
        value_str = cls._get_config(key)
        return value_str

    @classmethod
    def get_config_int(cls, key):
        value_str = cls._get_config(key)
        if value_str.isdigit():
            i_value = int(value_str)
            return i_value
        else:
            return None

    @classmethod
    def get_config_bool(cls, key):
        value_str = cls._get_config(key)
        if value_str.strip().lower() in ['true', 'yes', 'enable', '1']:
            return True
        else:
            return False
