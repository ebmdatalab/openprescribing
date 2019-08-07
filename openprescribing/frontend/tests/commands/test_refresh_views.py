from django.core.management import call_command
from django.test import TestCase


class RefreshViewsTestCase(TestCase):
    def test_basic_smoketest(self):
        # Test we can run it without it blowing up
        call_command("refresh_views")
