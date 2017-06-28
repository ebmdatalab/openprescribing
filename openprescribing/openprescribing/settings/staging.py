"""Production settings and globals."""

from __future__ import absolute_import
from .base import *
from common import utils


# DEBUG CONFIGURATION
# See: https://docs.djangoproject.com/en/dev/ref/settings/#debug
DEBUG = False  # Not so safe to set to True as staging is not behind a password
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

ANYMAIL["MAILGUN_SENDER_DOMAIN"] = "staging.openprescribing.net",
SUPPORT_EMAIL = 'feedback@staging.openprescribing.net'
DEFAULT_FROM_EMAIL = SUPPORT_EMAIL

# LOGGING CONFIGURATION
# See: https://docs.djangoproject.com/en/dev/ref/settings/#logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'formatters': {
        'verbose': {
            'format': ('%(asctime)s %(levelname)s [%(name)s:%(lineno)s] '
                       '%(module)s %(process)d %(thread)d %(message)s')
        }
    },
    'handlers': {
        'gunicorn': {
            'level': 'DEBUG',
            'class': 'logging.handlers.RotatingFileHandler',
            'formatter': 'verbose',
            'filename': "%s/logs/gunicorn.log" % INSTALL_ROOT,
            'maxBytes': 1024 * 1024 * 100,  # 100 mb
        },
        'signals': {
            'level': 'DEBUG',
            'class': 'logging.handlers.RotatingFileHandler',
            'formatter': 'verbose',
            'filename':
            "%s/logs/mail-signals.log" % INSTALL_ROOT,
            'maxBytes': 1024 * 1024 * 100,  # 100 mb
            }
    },
    'loggers': {
        'django': {
            'level': 'WARN',
            'handlers': ['gunicorn'],
            'propagate': True,
        },
        'frontend': {
            'level': 'DEBUG',
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
GOOGLE_OPTIMIZE_CONTAINER_ID = 'GTM-KRQSJM9'
