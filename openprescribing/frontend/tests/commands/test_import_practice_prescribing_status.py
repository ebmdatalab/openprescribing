import os
import unittest
from django.core.management import call_command
from django.test import TestCase
from frontend.models import Practice


def setUpModule():
        Practice.objects.create(code='A81044')
        Practice.objects.create(code='A81043')
        Practice.objects.create(code='J18105')


def tearDownModule():
    call_command('flush', verbosity=0, interactive=False)


class CommandsTestCase(TestCase):

    def test_import_practice_dispensing_status(self):
        args = []
        fname = 'frontend/tests/fixtures/commands/epraccur_sample.csv'
        opts = {
            'filename': fname
        }
        call_command('import_practice_prescribing_status', *args, **opts)
        p = Practice.objects.get(code='A81044')
        self.assertEqual(p.get_setting_display(), 'GP Practice')
        p = Practice.objects.get(code='A81043')
        self.assertEqual(p.get_setting_display(), 'Prison')
        p = Practice.objects.get(code='J18105')
        self.assertEqual(p.get_setting_display(), 'Unknown')
