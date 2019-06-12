from django.test import TestCase


class ApiTestUtils(TestCase):

    def test_param_to_list(self):
        from api.view_utils import param_to_list

        self.assertEquals(param_to_list('foo'), ['foo'])
        self.assertEquals(param_to_list('foo,bar'), ['foo', 'bar'])
        self.assertEquals(param_to_list(None), [])
        self.assertEquals(param_to_list([]), [])
