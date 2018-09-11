import hipposhop.settings.globalvar as gl


# 注意: 配置文件设置需要放到引入common.py之前
gl._init()
gl.set_value('app_config', 'config/config_dev.ini')

# 引入common配置
from hipposhop.settings.common import *

DEBUG = True
ALLOWED_HOSTS = ["*"]


# Database
# https://docs.djangoproject.com/en/2.0/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': DB_NAME,
        'USER': DB_USER,
        'PASSWORD': DB_PASSWORD,
        'HOST': DB_HOST,
        'PORT': '3306',
        'OPTIONS': {
            'charset': 'utf8mb4',
          },
        'TEST': {
            'ENGINE': 'django.db.backends.mysql',
            'CHARSET': 'utf8mb4',
            'COLLATION': 'utf8mb4_unicode_ci',
        }
    },

}


CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': [DJANGO_REDIS_LOCATION, ],
        'OPTIONS': {
            'DB': DJANGO_REDIS_DB,
            'PASSWORD': DJANGO_REDIS_PASSWORD,
            'PARSER_CLASS': 'redis.connection.HiredisParser',
            'CONNECTION_POOL_CLASS': 'redis.BlockingConnectionPool',
            'CONNECTION_POOL_CLASS_KWARGS': {
                'max_connections': 50,
                'timeout': 20,
            },
            'MAX_CONNECTIONS': 100,
            'PICKLE_VERSION': -1,
        },
    },
}

CUBES_REDIS_TIMEOUT = 60*60



DEBUG_PERF = False

if DEBUG_PERF:
    MIDDLEWARE += ['silk.middleware.SilkyMiddleware',]

    INSTALLED_APPS += [
        'silk',
        ]

    SILKY_PYTHON_PROFILER = True
    SILKY_PYTHON_PROFILER_BINARY = True
    SILKY_PYTHON_PROFILER_RESULT_PATH = 'profiles/'
    SILKY_META = True
    SILKY_INTERCEPT_PERCENT = 50

