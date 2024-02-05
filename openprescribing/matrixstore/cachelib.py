"""
Provides a basic caching decorator with a few special features:

    * Arguments must all be either one of the basic types defined below or have
      a `cache_key` attribute which identifies the state of the object for
      caching purposes. Passing in anything else is an error.

    * There is no time-based expiration: the intention is that the decorator
      should only be applied to functions whose output is purely determined by
      their arguments. If the logic of the function changes then the `version`
      argument can be incremented.
"""

import functools

from django.core.cache import cache as default_cache

MISSING = object()
BASIC_TYPES = (bool, int, float, str)


def memoize(version=1, cache=default_cache):
    def decorator(func):
        cache_key_base = _get_cache_key_base(func, version)

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            cache_key = _get_cache_key(cache_key_base, args, kwargs)
            result = cache.get(cache_key, default=MISSING)
            if result is MISSING:
                result = func(*args, **kwargs)
                cache.set(cache_key, result)
            return result

        return wrapper

    return decorator


def _get_cache_key_base(func, version):
    return "{}.{}:{}".format(func.__module__, func.__qualname__, version)


def _get_cache_key(base, args, kwargs):
    args = list(map(_get_object_cache_key, args))
    kwargs = [(k, _get_object_cache_key(v)) for (k, v) in sorted(kwargs.items())]
    return base, args, kwargs


def _get_object_cache_key(value):
    if isinstance(value, BASIC_TYPES):
        return value
    cache_key = getattr(value, "cache_key", None)
    if cache_key is None:
        raise ValueError(
            "Received an object of type {} with no cache_key attribute".format(
                type(value)
            )
        )
    return cache_key
