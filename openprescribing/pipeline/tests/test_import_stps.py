import os
from django.conf import settings
from django.core.management import call_command
from django.test import TestCase
from frontend.models import PCT, STP


class TestImportSTPs(TestCase):
    def test_import_stps(self):
        # These CCGs are all referred to in stps.csv
        for code in ['02N', '02W', '02Y', '03F', '00T', '00V']:
            PCT.objects.create(code=code, name='CCG ' + code, org_type='CCG')

        # This STP will be unchanged
        STP.objects.create(ons_code='E54000005', name='West Yorkshire')

        # This STP's name will be updated
        STP.objects.create(ons_code='E54000006', name='Humber')

        path = os.path.join(settings.APPS_ROOT, 'pipeline', 'test-data', 'stps.csv')
        call_command('import_stps', '--filename', path)

        for ons_code, name in [
            ['E54000005', 'West Yorkshire'],
            ['E54000006', 'Humber, Coast and Vale'],
            ['E54000007', 'Greater Manchester'],
        ]:
            stp = STP.objects.get(ons_code=ons_code)
            self.assertEqual(stp.name, name)

        for ccg_code, stp_ons_code in [
            ['02N', 'E54000005'],
            ['02W', 'E54000005'],
            ['02Y', 'E54000006'],
            ['03F', 'E54000006'],
            ['00T', 'E54000007'],
            ['00V', 'E54000007'],
        ]:
            ccg = PCT.objects.get(code=ccg_code)
            self.assertEqual(ccg.stp.ons_code, stp_ons_code)
