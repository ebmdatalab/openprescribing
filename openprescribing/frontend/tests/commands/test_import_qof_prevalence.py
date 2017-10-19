import os
import unittest
from django.core.management import call_command
from django.test import TestCase
from frontend.models import PCT, Practice, QOFPrevalence


def setUpModule():
    PCT.objects.create(code='00C')
    PCT.objects.create(code='00D')
    Practice.objects.create(code='A81001')
    Practice.objects.create(code='A81002')
    Practice.objects.create(code='A81003')
    Practice.objects.create(code='A81004')


def tearDownModule():
    call_command('flush', verbosity=0, interactive=False)


class CommandsTestCase(TestCase):
    def test_import_qof_prevalence(self):
        args = []
        fixture_dir = 'frontend/tests/fixtures/commands/'
        opts = {
            'by_ccg': fixture_dir + 'prevalencebyccg.csv',
            'by_practice': fixture_dir + 'prevalencebyprac.csv',
            'start_year': 2013
        }
        call_command('import_qof_prevalence', *args, **opts)

        ccg = PCT.objects.get(code='00C')
        qof_for_ccg = QOFPrevalence.objects.filter(pct=ccg)
        self.assertEqual(qof_for_ccg.count(), 24)
        qof_dementia = qof_for_ccg.get(indicator_group='DEM')
        self.assertEqual(qof_dementia.disease_register_size, 977)

        practice = Practice.objects.get(code='A81002')
        qof_for_practice = QOFPrevalence.objects.filter(practice=practice)
        self.assertEqual(qof_for_practice.count(), 24)
        qof_dementia = qof_for_practice.get(indicator_group='DEM')
        self.assertEqual(qof_dementia.disease_register_size, 171)
