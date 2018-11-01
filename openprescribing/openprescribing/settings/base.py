"""Common settings and globals."""
from os.path import abspath, basename, dirname, join, normpath
from sys import path
from common import utils

# PATH CONFIGURATION
# Absolute filesystem path to the Django project directory:
SETTINGS_ROOT = dirname(dirname(abspath(__file__)))

# Absolute filesystem path to the top-level project folder:
APPS_ROOT = dirname(SETTINGS_ROOT)

REPO_ROOT = abspath(join(APPS_ROOT, '..'))

# Site name:
SITE_NAME = basename(SETTINGS_ROOT)

# Site ID (django.contrib.sites framework, required by django-anyauth
SITE_ID = 1

# Add our project to our pythonpath, this way we don't need to type our project
# name in our dotted import paths:
path.append(SETTINGS_ROOT)
# END PATH CONFIGURATION


# DEBUG CONFIGURATION
# See: https://docs.djangoproject.com/en/dev/ref/settings/#debug
DEBUG = False
# END DEBUG CONFIGURATION


# MANAGER CONFIGURATION
# See: https://docs.djangoproject.com/en/dev/ref/settings/#admins
ADMINS = (
    ('EBM Data Lab', 'tech@ebmdatalab.net'),
)

# See: https://docs.djangoproject.com/en/dev/ref/settings/#managers
MANAGERS = ADMINS
# END MANAGER CONFIGURATION


# GENERAL CONFIGURATION
# See: https://docs.djangoproject.com/en/dev/ref/settings/#time-zone
TIME_ZONE = 'Europe/London'

# See: https://docs.djangoproject.com/en/dev/ref/settings/#language-code
LANGUAGE_CODE = 'en-gb'

# See: https://docs.djangoproject.com/en/dev/ref/settings/#site-id
SITE_ID = 1

# See: https://docs.djangoproject.com/en/dev/ref/settings/#use-i18n
USE_I18N = False

# See: https://docs.djangoproject.com/en/dev/ref/settings/#use-l10n
USE_L10N = True

# See: https://docs.djangoproject.com/en/dev/ref/settings/#use-tz
USE_TZ = True
# END GENERAL CONFIGURATION


# MEDIA CONFIGURATION
# See: https://docs.djangoproject.com/en/dev/ref/settings/#media-root
MEDIA_ROOT = normpath(join(APPS_ROOT, 'media'))

# See: https://docs.djangoproject.com/en/dev/ref/settings/#media-url
MEDIA_URL = '/media/'
# END MEDIA CONFIGURATION


# STATIC FILE CONFIGURATION

# The directory from where files should be served. The `collectstatic`
# command will copy all files from static folders to here for serving.
# The reason we need to do this (rather than just serve things
# straignt from a static directory) is because dependent apps may also
# provide static files for serving -- specifically, the Django admin
# app.
# See: https://docs.djangoproject.com/en/dev/ref/settings/#static-root
STATIC_ROOT = normpath(join(APPS_ROOT, 'assets'))

# The base URL which will be used in URLs for static assets
# See: https://docs.djangoproject.com/en/dev/ref/settings/#static-url
STATIC_URL = '/static/'

# Places that are searched -- by the django development server ahd the
# `collectstatic` command -- for static files
# See:
# https://docs.djangoproject.com/en/dev/ref/contrib/staticfiles/#std:setting-STATICFILES_DIRS
STATICFILES_DIRS = (
    normpath(join(APPS_ROOT, 'static')),
)

# See:
# https://docs.djangoproject.com/en/dev/ref/contrib/staticfiles/#staticfiles-finders
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
)
# END STATIC FILE CONFIGURATION


# SECRET CONFIGURATION
# See: https://docs.djangoproject.com/en/dev/ref/settings/#secret-key
SECRET_KEY = utils.get_env_setting('SECRET_KEY')
# END SECRET CONFIGURATION

# SITE CONFIGURATION
# Hosts/domain names that are valid for this site
# See https://docs.djangoproject.com/en/1.5/ref/settings/#allowed-hosts
ALLOWED_HOSTS = []
# END SITE CONFIGURATION


# FIXTURE CONFIGURATION
# See:
# https://docs.djangoproject.com/en/dev/ref/settings/#std:setting-FIXTURE_DIRS
FIXTURE_DIRS = (
    normpath(join(APPS_ROOT, 'frontend', 'tests', 'fixtures')),
)
# END FIXTURE CONFIGURATION


# TEMPLATE CONFIGURATION
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            normpath(join(APPS_ROOT, 'templates')),
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.contrib.auth.context_processors.auth',
                'django.template.context_processors.debug',
                'django.template.context_processors.i18n',
                'django.template.context_processors.media',
                'django.template.context_processors.static',
                'django.template.context_processors.tz',
                'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.request',
                'frontend.context_processors.support_email',
                'frontend.context_processors.google_tracking_id',
                'frontend.context_processors.api_host',
                'frontend.context_processors.debug'
            ],
            'debug': DEBUG
        },
    },
]
# END TEMPLATE CONFIGURATION


# MIDDLEWARE CONFIGURATION
# See: https://docs.djangoproject.com/en/dev/ref/settings/#middleware-classes
MIDDLEWARE_CLASSES = (
    'corsheaders.middleware.CorsMiddleware',
    # Default Django middleware.
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'corsheaders.middleware.CorsPostCsrfMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    # 'django.middleware.clickjacking.XFrameOptionsMiddleware',
)
# END MIDDLEWARE CONFIGURATION


# URL CONFIGURATION
# See: https://docs.djangoproject.com/en/dev/ref/settings/#root-urlconf
ROOT_URLCONF = '%s.urls' % SITE_NAME
# END URL CONFIGURATION


# APP CONFIGURATION
DJANGO_APPS = (
    # Default Django apps:
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.gis',
    # Useful template tags:
    'django.contrib.humanize',
    'rest_framework',
    'corsheaders',
)

# Apps specific for this project go here.
LOCAL_APPS = (
    'frontend',
    'dmd',
    'pipeline',
    'gcutils',
)

CONTRIB_APPS = (
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    # 'allauth.socialaccount.providers.facebook',
    # 'allauth.socialaccount.providers.google',
    'allauth.socialaccount.providers.twitter',
    'anymail',
    'crispy_forms',
    'raven.contrib.django.raven_compat',
    'import_export'
)

# See: https://docs.djangoproject.com/en/dev/ref/settings/#installed-apps
INSTALLED_APPS = DJANGO_APPS + CONTRIB_APPS + LOCAL_APPS
# END APP CONFIGURATION


# LOGGING CONFIGURATION
# See: https://docs.djangoproject.com/en/dev/ref/settings/#logging
# A sample logging configuration. The only tangible logging
# performed by this configuration is to send an email to
# the site admins on every HTTP 500 error when DEBUG=False.
# See http://docs.djangoproject.com/en/dev/topics/logging for
# more details on how to customize your logging configuration.
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': ('%(asctime)s %(levelname)s '
                       '[%(name)s:%(lineno)s] %(module)s '
                       '%(process)d %(thread)d %(message)s')
        }
    },
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse'
        }
    },
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler'
        }

    },
    'loggers': {
        'django.request': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': True,
        }
    }
}
# END LOGGING CONFIGURATION


AUTHENTICATION_BACKENDS = (
    # Needed to login by username in Django admin, regardless of `allauth`
    'django.contrib.auth.backends.ModelBackend',
    # `allauth` specific authentication methods, such as login by e-mail
    'allauth.account.auth_backends.AuthenticationBackend',
    # custom backend to support logging in via a hash
    'frontend.backends.SecretKeyBackend'
)


# WSGI CONFIGURATION
# See: https://docs.djangoproject.com/en/dev/ref/settings/#wsgi-application
WSGI_APPLICATION = '%s.wsgi.application' % SITE_NAME
# END WSGI CONFIGURATION

TEST_RUNNER = 'frontend.tests.custom_runner.AssetBuildingTestRunner'

CONN_MAX_AGE = 1200


REST_FRAMEWORK = {
    'DEFAULT_RENDERER_CLASSES': (
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',
        'rest_framework_csv.renderers.CSVRenderer',
    ),
    'DEFAULT_CONTENT_NEGOTIATION_CLASS':
    'frontend.negotiation.IgnoreAcceptsContentNegotiation',
}

CORS_URLS_REGEX = r'^/api/.*$'
CORS_ORIGIN_ALLOW_ALL = True
CORS_ALLOW_METHODS = (
    'GET'
)
SUPPORT_TO_EMAIL = 'ebmdatalab@phc.ox.ac.uk'
SUPPORT_FROM_EMAIL = 'feedback@openprescribing.net'
DEFAULT_FROM_EMAIL = 'OpenPrescribing <{}>'.format(SUPPORT_FROM_EMAIL)
GDOC_DOCS = {
    'zooming': '1lz1uRfNOy2fQ-xSy_6BiLV_7Mgr-Z2V0-VWzo6HlCO0',
    'analyse': '1HqlJlUA86cnlyJpUxiQdGsM46Gsv9xyZkmhkTqjbwH0',
    'analyse-by-practice': '1idnk9yczLLBLbYUbp06dMglfivobTNoKY7pA2zCDPI8',
    'analyse-by-ccg': '1izun1jIGW7Wica-eMkUOU1x7RWqCZ9BJrbWNvsCzWm0'
}

API_HOST = utils.get_env_setting('API_HOST', default='')

# BigQuery project name
BQ_PROJECT = 'ebmdatalab'

# BigQuery dataset names
BQ_HSCIC_DATASET = 'hscic'
BQ_MEASURES_DATASET = 'measures'
BQ_TMP_EU_DATASET = 'tmp_eu'
BQ_DMD_DATASET = 'dmd'
BQ_ARCHIVE_DATASET = 'archive'

# Other BQ settings
BQ_DEFAULT_TABLE_EXPIRATION_MS = None
BQ_LOCATION = 'EU'

# Use django-anymail through mailgun for sending emails
EMAIL_BACKEND = "anymail.backends.mailgun.EmailBackend"
ANYMAIL = {
    "MAILGUN_API_KEY": utils.get_env_setting('MAILGUN_API_KEY'),
    "MAILGUN_SENDER_DOMAIN": "staging.openprescribing.net",
    "WEBHOOK_SECRET": "%s:%s" % (
        utils.get_env_setting('MAILGUN_WEBHOOK_USER'),
        utils.get_env_setting('MAILGUN_WEBHOOK_PASS'))
}

# See: https://docs.djangoproject.com/en/dev/ref/settings/#server-email
SERVER_EMAIL = "errors@openprescribing.net"

# django-allauth configuration
ACCOUNT_ADAPTER = 'frontend.account.adapter.CustomAdapter'
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_EMAIL_VERIFICATION = "optional"
ACCOUNT_CONFIRM_EMAIL_ON_GET = True
ACCOUNT_LOGIN_ON_EMAIL_CONFIRMATION = True
ACCOUNT_EMAIL_CONFIRMATION_EXPIRE_DAYS = 7

LOGIN_REDIRECT_URL = "finalise-signup"
LOGIN_URL = "home"

# Easy bootstrap styling of Django forms
CRISPY_TEMPLATE_PACK = 'bootstrap3'

# For grabbing images that we insert into alert emails
GRAB_HOST = "https://openprescribing.net"

# For sending messages to Slack
SLACK_GENERAL_POST_KEY = utils.get_env_setting(
    'SLACK_GENERAL_POST_KEY',
    default=''
)
SLACK_SENDING_ACTIVE = True

# Newsletter signup
MAILCHIMP_LIST_ID = 'b2b7873a73'

sentry_raven_dsn = utils.get_env_setting('SENTRY_RAVEN_DSN', default='')
if sentry_raven_dsn:
    RAVEN_CONFIG = {'dsn': sentry_raven_dsn}
