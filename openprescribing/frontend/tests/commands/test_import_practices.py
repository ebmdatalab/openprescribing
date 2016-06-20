from django.core.management import call_command
from django.test import TestCase
from frontend.models import Practice, PCT, SHA
import datetime


def setUpModule():
    PCT.objects.create(code='00M', name='SOUTHPORT AND FORMBY CCG')
    PCT.objects.create(code='00K', name='SOUTH MANCHESTER CCG')
    SHA.objects.create(code='Q74', name='TEST AREA TEAM')


def tearDownModule():
    call_command('flush', verbosity=0, interactive=False)


class CommandsTestCase(TestCase):

    def test_import_practices_from_epraccur(self):

        args = []
        epraccur = 'frontend/tests/fixtures/commands/'
        epraccur += 'epraccur_sample.csv'
        opts = {
            'epraccur': epraccur
        }
        call_command('import_practices', *args, **opts)

        # Test import from epraccur.
        p = Practice.objects.get(code='A81043')
        self.assertEqual(p.ccg.code, '00M')
        self.assertEqual(p.name, 'THE MANOR HOUSE SURGERY')
        addr = 'THE MANOR HOUSE SURGERY, BRAIDWOOD ROAD, NORMANBY, '
        addr += 'MIDDLESBROUGH, CLEVELAND, TS6 0HA'
        self.assertEqual(p.address_pretty(), addr)
        self.assertEqual(p.postcode, 'TS6 0HA')
        self.assertEqual(p.open_date, datetime.date(1974, 4, 1))
        self.assertEqual(p.close_date, None)
        self.assertEqual(p.status_code, 'A')
        self.assertEqual(p.join_provider_date, datetime.date(2013, 4, 1))
        self.assertEqual(p.leave_provider_date, None)
        self.assertEqual(p.get_setting_display(), 'Prison')

        p = Practice.objects.get(code='A81044')
        self.assertEqual(p.ccg.code, '00K')
        self.assertEqual(p.get_setting_display(), 'GP Practice')

        p = Practice.objects.get(code='Y01063')
        self.assertEqual(p.ccg, None)

    def test_import_practices_from_hscic(self):

        args = []
        hscic = 'frontend/tests/fixtures/commands/hscic_practices.csv'
        opts = {
            'hscic_address': hscic
        }
        call_command('import_practices', *args, **opts)

        p = Practice.objects.get(code='A81001')
        self.assertEqual(p.name, 'THE DENSHAM SURGERY')
        addr = "THE HEALTH CENTRE, LAWSON STREET, "
        addr += "STOCKTON, CLEVELAND, TS18 1HU"
        self.assertEqual(p.address_pretty(), addr)
        self.assertEqual(p.open_date, None)
        self.assertEqual(p.ccg, None)
