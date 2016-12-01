from __future__ import absolute_import
import os

from .base import *

DEBUG = True
TEMPLATES[0]['OPTIONS']['debug'] = DEBUG
DATABASES = {
    'default': {
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'NAME': utils.get_env_setting('DB_NAME'),
        'USER': utils.get_env_setting('DB_USER'),
        'PASSWORD': utils.get_env_setting('DB_PASS'),
        'HOST': utils.get_env_setting('DB_HOST', '127.0.0.1')
    }
}
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    }
}
INTERNAL_IPS = ('127.0.0.1',)
ANYMAIL = {
    "MAILGUN_API_KEY": "key-b503fcc6f1c029088f2b3f9b3faa303c",
    "MAILGUN_SENDER_DOMAIN": "staging.openprescribing.net",
    "WEBHOOK_AUTHORIZATION": "%s" % utils.get_env_setting(
        'MAILGUN_WEBHOOK_AUTH_STRING', 'example:foo'),
}

EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'

if 'TRAVIS' not in os.environ:
    LOGGING = {
        'version': 1,
        'disable_existing_loggers': True,
        'handlers': {
            'file': {
                'level': 'DEBUG',
                'class': 'logging.FileHandler',
                'filename': '../log/test-debug.log',
            },
        },
        'loggers': {
            'django': {
                'handlers': ['file'],
                'level': 'DEBUG',
                'propagate': True,
            },
        },
    }
# Prefix table names with `test_` to prevent namespace clashes in
# BigQuery
BQ_CCG_TABLE_PREFIX = 'test_' + BQ_CCG_TABLE_PREFIX
BQ_GLOBALS_TABLE_PREFIX = 'test_' + BQ_GLOBALS_TABLE_PREFIX
BQ_PRACTICE_TABLE_PREFIX = 'test_' + BQ_PRACTICE_TABLE_PREFIX
BQ_PRESCRIBING_TABLE_NAME = 'test_' + BQ_PRESCRIBING_TABLE_NAME
BQ_PRACTICES_TABLE_NAME = 'test_' + BQ_PRACTICES_TABLE_NAME
BQ_FULL_PRACTICES_TABLE_NAME = "[%s:measures.%s]" % (
    BQ_PROJECT, BQ_PRACTICES_TABLE_NAME)

# For grabbing images that we insert into alert emails
GRAB_HOST = "http://localhost"

# This is the same as the dev/local one
GOOGLE_TRACKING_ID = 'UA-62480003-2'
