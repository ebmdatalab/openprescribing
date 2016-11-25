import datetime
from django.core.management import call_command
from django.db import InternalError
from django.test import TestCase
from frontend.models import Chemical, PCT, Practice
from frontend.models import Prescription, SHA, ImportLog
from common import utils
from mock import patch


class CommandsTestCase(TestCase):
    def setUp(self):
        self.chemical = Chemical.objects.create(
            bnf_code='0401020K0', chem_name='test')
        self.practice = Practice.objects.create(code='Y03375', name='test')
        self.pct = PCT.objects.create(code='5D7', name='test')
        self.sha = SHA.objects.create(code='Q30', name='test')
        Chemical.objects.create(bnf_code='0410030C0', chem_name='test')
        Practice.objects.create(code='Y00135', name='test')
        Practice.objects.create(code='Y01957', name='test')

        test_file = 'frontend/tests/fixtures/commands/'
        test_file += 'T201304PDPI+BNFT_formatted.CSV'
        self.new_opts = {
            'filename': test_file
        }
        db_name = 'test_' + utils.get_env_setting('DB_NAME')
        self.env = patch.dict(
            'os.environ', {'DB_NAME': db_name})
        with self.env:
            call_command('import_hscic_prescribing', **self.new_opts)

    def test_import_drops_existing(self):
        with self.env:
            call_command('import_hscic_prescribing', **self.new_opts)
        self.assertEqual(Prescription.objects.count(), 15)

    def test_inserts_fail(self):
        with self.assertRaises(InternalError):
            Prescription.objects.create(
                sha=self.sha, pct=self.pct, practice=self.practice,
                chemical=self.chemical, presentation_code='0000',
                presentation_name='asd', total_items=4,
                actual_cost=4, quantity=4,
                processing_date='2013-04-01')

    def test_import_creates_prescriptions(self):
        shas = SHA.objects.all()
        self.assertEqual(shas.count(), 1)
        pcts = PCT.objects.all()
        self.assertEqual(pcts.count(), 1)

        prescriptions = Prescription.objects.all()
        self.assertEqual(prescriptions.count(), 15)

        p = Prescription.objects.filter(presentation_code='0401020K0AAAIAI')
        self.assertEqual(p.count(), 3)

        p = Prescription.objects.get(presentation_code='0410030C0AAAFAF')
        self.assertEqual(p.sha.code, 'Q30')
        self.assertEqual(p.pct.code, '5D7')
        self.assertEqual(p.practice.code, 'Y01957')
        self.assertEqual(p.chemical.bnf_code, '0410030C0')
        self.assertEqual(p.presentation_name, 'Methadone HCl_Mix 1mg/1ml S/F')
        self.assertEqual(p.total_items, 1346)
        self.assertEqual(p.actual_cost, 11270.33)
        self.assertEqual(p.quantity, 878870)
        self.assertEqual(p.processing_date, datetime.date(2013, 4, 1))
        l = ImportLog.objects.latest_in_category('prescribing')
        self.assertEqual(l.current_at.strftime('%Y-%m-%d'), '2013-04-01')
