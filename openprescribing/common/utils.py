import hashlib
import uuid
from os import environ
from django.core.exceptions import ImproperlyConfigured
from django import db


def get_env_setting(setting, default=None):
    """ Get the environment setting.

    Return the default, or raise an exception if none supplied
    """
    try:
        return environ[setting]
    except KeyError:
        if default:
            return default
        else:
            error_msg = "Set the %s env variable" % setting
            raise ImproperlyConfigured(error_msg)


def under_test():
    return db.connections.databases['default']['NAME'].startswith("test_")


def google_user_id(user):
    if user:
        h = hashlib.md5()
        h.update(str(user.id))
        client_id = str(uuid.UUID(h.hexdigest()))
    else:
        client_id = None
    return client_id
