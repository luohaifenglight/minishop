import hipposhop.settings.globalvar as gl

# 注意: 配置文件设置需要放到引入common.py之前
gl._init()
gl.set_value('app_config', 'config/config_test.ini')

# 引入common配置
from hipposhop.settings.common import *


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

APP_LOG_DIR = "/tmp/log"

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '%(asctime)s %(levelname)s %(process)d %(module)s:%(funcName)s %(message)s'
        },
        'simple': {
            'format': '%(levelname)s %(message)s'
        },
    },
    'filters': {
        'require_debug_true': {
            '()': 'django.utils.log.RequireDebugTrue',
        }, # 针对 DEBUG = True 的情况
    },
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'filters': ['require_debug_true'],
            'class': 'logging.StreamHandler',
            'formatter': 'simple'
        },
        'file_handler': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(APP_LOG_DIR, 'debug.log'),
            'maxBytes': 1024 * 1024 * 5,  # 5 MB
            'backupCount': 200,
            'formatter': 'verbose'
        },
        'mail_admins': {
            'level': 'ERROR',
            'class': 'django.utils.log.AdminEmailHandler',
            'include_html' : True,
            'formatter': 'verbose'
        }
    },
    'loggers': {
        'django': {
            'handlers' :[ 'console', 'file_handler'],
            'level': os.getenv('DJANGO_LOG_LEVEL', 'INFO'),
            'propagate': True, #是否继承父类的log信息
        },
        'django.request': {
            'handlers': ['console', 'file_handler', 'mail_admins'],
            'level': os.getenv('DJANGO_LOG_LEVEL', 'INFO'),
            'propagate': False,
        },
        'project.custom': {
            'handlers': ['console', 'mail_admins'],
            'level': 'INFO',

        }
    }
}

