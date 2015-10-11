import os
import unittest
from django.core.management import call_command
from django.test import TestCase
from frontend.models import Practice


def setUpModule():
    pass


def tearDownModule():
    call_command('flush', verbosity=0, interactive=False)


class CommandsTestCase(TestCase):

    def test_import_hscic_prescribing(self):
        args = []
        practice_file = 'frontend/tests/fixtures/commands/hscic_practices.csv'
        opts = {
            'practice_file': practice_file
        }
        call_command('import_hscic_practices', *args, **opts)

        practices = Practice.objects.all()
        self.assertEqual(practices.count(), 27)
        practice = Practice.objects.get(code='A81014')
        self.assertEqual(practice.name, 'QUEENSTREE PRACTICE')
        addr1 = "THE HEALTH CENTRE, QUEENSWAY, BILLINGHAM, CLEVELAND, TS23 2LA"
        addr2 = "QUEENSWAY, BILLINGHAM, CLEVELAND, TS23 2LA"
        self.assertEqual(practice.address_pretty(), addr1)
        self.assertEqual(practice.address_pretty_minus_firstline(),
                         addr2)
