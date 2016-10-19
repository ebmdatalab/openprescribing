"""Production settings and globals."""

from __future__ import absolute_import
from .base import *
from common import utils


# HOST CONFIGURATION
# See:
# https://docs.djangoproject.com/en/1.5/releases/1.5/#allowed-hosts-required-in-production
ALLOWED_HOSTS = ['openprescribing.net', 'openprescriptions.net', ]
# END HOST CONFIGURATION

# See: https://docs.djangoproject.com/en/dev/ref/settings/#email-subject-prefix
EMAIL_SUBJECT_PREFIX = '[%s] ' % SITE_NAME

# END EMAIL CONFIGURATION

# DATABASE CONFIGURATION
DATABASES = {
    'default': {
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'NAME': utils.get_env_setting('DB_NAME'),
        'USER': utils.get_env_setting('DB_USER'),
        'PASSWORD': utils.get_env_setting('DB_PASS'),
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
