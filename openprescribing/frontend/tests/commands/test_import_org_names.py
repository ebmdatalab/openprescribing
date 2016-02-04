import os
import unittest
from django.core.management import call_command
from django.test import TestCase
from frontend.models import SHA, PCT


def setUpModule():
        SHA.objects.create(code='Q48')
        PCT.objects.create(code='06F',
                           name='NHS Bedfordshire')


def tearDownModule():
    call_command('flush', verbosity=0, interactive=False)


class CommandsTestCase(TestCase):

    def test_import_org_names(self):

        args = []
        opts = {
            'area_team': 'data/org_codes/at.csv',
            'ccg': 'data/org_codes/CCG_APR_2013.csv',
            'area_team_to_ccg': 'data/org_codes/CCG13_NHSAT13_NHSCR13_EW_LU.csv'
        }
        data_dir = 'data/org_codes'
        call_command('import_org_names', *args, **opts)

        area_teams = SHA.objects.filter()
        self.assertEqual(area_teams.count(), 25)
        lincs_at = SHA.objects.get(code='Q59')
        self.assertEqual(lincs_at.name, 'Leicestershire and Lincolnshire')
        self.assertEqual(lincs_at.ons_code, 'E39000016')

        ccgs = PCT.objects.filter(org_type='CCG')
        self.assertEqual(ccgs.count(), 211)
        lincs_ccg = PCT.objects.get(code='03T')
        self.assertEqual(lincs_ccg.name, 'NHS Lincolnshire East')
        self.assertEqual(lincs_ccg.ons_code, 'E38000099')

        ccgs_in_lincs_at = PCT.objects.filter(managing_group=lincs_at)
        self.assertEqual(ccgs_in_lincs_at.count(), 7)
