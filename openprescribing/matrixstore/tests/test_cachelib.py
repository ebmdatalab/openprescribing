from mock import Mock
import warnings

from django.core.cache import CacheKeyWarning
from django.test import SimpleTestCase, override_settings

from matrixstore.cachelib import memoize

# The local memory cache backend we use in testing warns that our binary cache
# keys won't be compatible with memcached, but we really don't care
warnings.simplefilter("ignore", CacheKeyWarning)


class MyTestObject:
    cache_key = None
    value = "hello"


@override_settings(
    CACHES={"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}}
)
class MemoizeDecoratorTest(SimpleTestCase):
    def test_cached_function_with_basic_arguments(self):
        test_func = Mock(
            side_effect=lambda *args, **kwargs: (args, kwargs), __qualname__="test_func"
        )
        cached_func = memoize()(test_func)
        result = cached_func("bar", foo=12, flag=True)
        self.assertEqual(result, (("bar",), {"foo": 12, "flag": True}))
        result2 = cached_func("bar", foo=12, flag=True)
        self.assertEqual(result2, result)
        test_func.assert_called_once_with("bar", foo=12, flag=True)

    def test_non_basic_arguments_with_cache_key_attr(self):
        test_func = Mock(side_effect=lambda arg: arg.value, __qualname__="test_func2")
        cached_func = memoize()(test_func)
        # Make an object to use as an argument and give it a cache key
        test_arg = MyTestObject()
        test_arg.cache_key = b"123556789"
        result = cached_func(test_arg)
        self.assertEqual(result, "hello")
        result2 = cached_func(test_arg)
        self.assertEqual(result2, result)
        test_func.assert_called_once_with(test_arg)

        # Make a new argument with a different cache_key
        new_test_arg = MyTestObject()
        new_test_arg.cache_key = b"987654321"
        cached_func(new_test_arg)
        # Check that this results in a new call to the wrapped function
        test_func.assert_called_with(new_test_arg)
        self.assertEqual(test_func.call_count, 2)

    def test_non_basic_arguments_without_cache_key_raise_error(self):
        def test_func(arg):
            return "foo"

        cached_func = memoize()(test_func)
        some_dict_arg = {}
        with self.assertRaises(ValueError):
            cached_func(some_dict_arg)
        # This object should have a cache_key attribute but without a value so
        # it should still raise an error
        test_arg = MyTestObject()
        with self.assertRaises(ValueError):
            cached_func(test_arg)
