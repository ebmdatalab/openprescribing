from django.test import TestCase


class ApiTestUtils(TestCase):
    def test_param_to_list(self):
        from api.view_utils import param_to_list

        self.assertEqual(param_to_list("foo"), ["foo"])
        self.assertEqual(param_to_list("foo,bar"), ["foo", "bar"])
        self.assertEqual(param_to_list(None), [])
        self.assertEqual(param_to_list([]), [])
