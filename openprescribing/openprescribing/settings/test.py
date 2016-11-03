from __future__ import absolute_import

from .local import *

EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'

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

# For grabbing images that we insert into alert emails
GRAB_HOST = "http://localhost"

# This is the same as the dev/local one
GOOGLE_TRACKING_ID = 'UA-62480003-2'
