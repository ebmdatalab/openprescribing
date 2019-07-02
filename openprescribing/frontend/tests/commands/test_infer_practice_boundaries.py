from django.core.management import call_command
from django.test import TestCase

from frontend.models import Practice


class InferPracticeBoundariesTestCase(TestCase):

    fixtures = ['orgs', 'practices']

    def test_basic_smoketest(self):
        should_have_boundary = Practice.objects.filter(
            setting=4, location__isnull=False
        )
        has_boundary = Practice.objects.filter(boundary__isnull=False)
        self.assertGreater(should_have_boundary.count(), 0)
        self.assertEqual(has_boundary.count(), 0)
        call_command('infer_practice_boundaries')
        self.assertEqual(has_boundary.count(), should_have_boundary.count())
