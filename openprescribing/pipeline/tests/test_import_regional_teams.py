import os
from django.conf import settings
from django.core.management import call_command
from django.test import TestCase
from frontend.models import RegionalTeam


class TestImportRegionalTeams(TestCase):
    def test_import_stps(self):
        path = os.path.join(settings.APPS_ROOT, 'pipeline', 'test-data', 'eauth.csv')
        call_command('import_regional_teams', '--filename', path)

        self.assertEqual(RegionalTeam.objects.count(), 6)

        rt = RegionalTeam.objects.get(code='Y54')
        self.assertEqual(rt.name, 'NORTH OF ENGLAND COMMISSIONING REGION')
        self.assertEqual(str(rt.open_date), '2012-10-01')
        self.assertEqual(rt.close_date, None)

        rt = RegionalTeam.objects.get(code='Y57')
        self.assertEqual(str(rt.open_date), '2012-10-01')
        self.assertEqual(str(rt.close_date), '2018-03-31')
