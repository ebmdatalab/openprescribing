import os
import unittest
from django.core.management import call_command
from django.test import TestCase
from frontend.models import Chemical


def setUpModule():
    pass


def tearDownModule():
    call_command('flush', verbosity=0, interactive=False)


class CommandsTestCase(TestCase):

    def test_import_hscic_prescribing(self):
        args = []
        chem_file = 'frontend/tests/fixtures/commands/hscic_chemicals.csv'
        opts = {
            'chem_file': chem_file
        }
        call_command('import_hscic_chemicals', *args, **opts)

        chemicals = Chemical.objects.all()
        self.assertEqual(chemicals.count(), 100)
        chemical = Chemical.objects.get(bnf_code='0410000N0')
        self.assertEqual(chemical.chem_name, 'Unknown')
        chemical = Chemical.objects.get(bnf_code='0101010M0')
        self.assertEqual(chemical.chem_name, 'Magaldrate')
