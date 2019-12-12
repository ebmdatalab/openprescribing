from unittest import TestCase

from openprescribing.utils import partially_format


class PartiallyFormatTestCase(TestCase):
    def test_partially_format(self):
        template = "{foo} {bar} {baz}"
        self.assertEqual(
            partially_format(template, foo="abc", bar="xyz"), "abc xyz {baz}"
        )
