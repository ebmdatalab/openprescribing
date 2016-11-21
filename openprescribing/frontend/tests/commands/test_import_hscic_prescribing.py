import datetime
from django.core.management import call_command
from django.test import TestCase
from frontend.models import Chemical, PCT, Practice
from frontend.models import Prescription, SHA, ImportLog
from common import utils


def setUpModule():
    chemical = Chemical.objects.create(bnf_code='0401020K0', chem_name='test')
    Chemical.objects.create(bnf_code='0410030C0', chem_name='test')
    Practice.objects.create(code='Y00135', name='test')
    Practice.objects.create(code='Y01957', name='test')
    practice = Practice.objects.create(code='Y03375', name='test')
    pct = PCT.objects.create(code='5D7', name='test')
    sha = SHA.objects.create(code='Q30', name='test')
    Prescription.objects.create(sha=sha, pct=pct, practice=practice,
                                chemical=chemical,
                                presentation_code='0410030C0BBAABA',
                                presentation_name='Methadose_Oral Conc',
                                total_items=4,
                                actual_cost=44.12, quantity=588,
                                processing_date='2013-04-01',
                                price_per_unit=0.075)


def tearDownModule():
    call_command('flush', verbosity=0, interactive=False)


class CommandsTestCase(TestCase):

    def test_import_hscic_prescribing(self):
        args = []
        db_name = 'test_' + utils.get_env_setting('DB_NAME')
        db_user = utils.get_env_setting('DB_USER')
        db_pass = utils.get_env_setting('DB_PASS')
        test_file = 'frontend/tests/fixtures/commands/'
        test_file += 'T201304PDPI+BNFT_formatted.CSV'
        new_opts = {
            'db_name': db_name,
            'db_user': db_user,
            'db_pass': db_pass,
            'filename': test_file
        }
        call_command('import_hscic_prescribing', *args, **new_opts)

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
        self.assertEqual(p.price_per_unit, 0.0128236599269517)
        l = ImportLog.objects.latest_in_category('prescribing')
        self.assertEqual(l.current_at.strftime('%Y-%m-%d'), '2013-04-01')
