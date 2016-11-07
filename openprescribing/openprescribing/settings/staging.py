"""Production settings and globals."""

from __future__ import absolute_import
from .base import *
from common import utils


# DEBUG CONFIGURATION
# See: https://docs.djangoproject.com/en/dev/ref/settings/#debug
DEBUG = True
TEMPLATES[0]['OPTIONS']['debug'] = DEBUG
# END DEBUG CONFIGURATION

# HOST CONFIGURATION
# See:
# https://docs.djangoproject.com/en/1.5/releases/1.5/#allowed-hosts-required-in-production
ALLOWED_HOSTS = ['staging.openprescribing.net']
# END HOST CONFIGURATION


# DATABASE CONFIGURATION
DATABASES = {
    'default': {
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'NAME': utils.get_env_setting('DB_NAME', ''),
        'USER': utils.get_env_setting('DB_USER', ''),
        'PASSWORD': utils.get_env_setting('DB_PASS', ''),
        'HOST': utils.get_env_setting('DB_HOST', '127.0.0.1')
    }
}
# END DATABASE CONFIGURATION


# CACHE CONFIGURATION
# See: https://docs.djangoproject.com/en/dev/ref/settings/#caches
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    }
}
# END CACHE CONFIGURATION

ANYMAIL = {
    "MAILGUN_API_KEY": "key-b503fcc6f1c029088f2b3f9b3faa303c",
    "MAILGUN_SENDER_DOMAIN": "staging.openprescribing.net",
    "WEBHOOK_AUTHORIZATION": "%s" % utils.get_env_setting(
        'MAILGUN_WEBHOOK_AUTH_STRING' 'example:foo'),
}

# LOGGING CONFIGURATION
# See: https://docs.djangoproject.com/en/dev/ref/settings/#logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'formatters': {
        'verbose': {
            'format': '%(asctime)s %(levelname)s [%(name)s:%(lineno)s] %(module)s %(process)d %(thread)d %(message)s'
        }
    },
    'handlers': {
        'gunicorn': {
            'level': 'DEBUG',
            'class': 'logging.handlers.RotatingFileHandler',
            'formatter': 'verbose',
            'filename': '/webapps/openprescribing_staging/logs/gunicorn.log',
            'maxBytes': 1024 * 1024 * 100,  # 100 mb
        },
        'signals': {
            'level': 'DEBUG',
            'class': 'logging.handlers.RotatingFileHandler',
            'formatter': 'verbose',
            'filename': '/webapps/openprescribing_staging/logs/mail-signals.log',
            'maxBytes': 1024 * 1024 * 100,  # 100 mb
            }
    },
    'loggers': {
        'django.request': {
            'level': 'DEBUG',
            'handlers': ['gunicorn'],
            'propagate': True,
        },
        'frontend': {
            'level': 'WARN',
            'handlers': ['gunicorn'],
            'propagate': True,
        },
        'frontend.signals.handlers': {
            'level': 'DEBUG',
            'handlers': ['signals'],
            'propagate': False,
        },
    }
}

# For grabbing images that we insert into alert emails
GRAB_HOST = "http://staging.openprescribing.net"

GOOGLE_TRACKING_ID = 'UA-62480003-3'
