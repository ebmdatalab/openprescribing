from __future__ import absolute_import

from .local import *

LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'handlers': {
        'file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': '../log/test-debug.log',
        },
        'console': {
            'level': 'WARN',
            'class': 'logging.StreamHandler',
            'formatter': 'simple'
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file', 'console'],
            'level': 'DEBUG',
            'propagate': True,
        },
    },
}

# Prefix table names with `test_` to prevent namespace clashes in
# BigQuery
BQ_GLOBALS_TABLE_PREFIX = 'test_' + BQ_GLOBALS_TABLE_PREFIX
BQ_PRACTICES_TABLE_NAME = 'test_' + BQ_PRACTICES_TABLE_NAME
BQ_PRACTICE_TABLE_PREFIX = 'test_' + BQ_PRACTICE_TABLE_PREFIX
BQ_CCG_TABLE_PREFIX = 'test_' + BQ_CCG_TABLE_PREFIX
