import datetime
from django.core.management import call_command
from django.test import TestCase
from frontend.models import PCT, RegionalTeam


def setUpModule():
    RegionalTeam.objects.create(code='Y54')
    PCT.objects.create(code='06F',
                       name='NHS Bedfordshire')


def tearDownModule():
    call_command('flush', verbosity=0, interactive=False)


class CommandsTestCase(TestCase):

    def test_import_org_names(self):

        args = []
        opts = {
            'ccg': 'frontend/tests/fixtures/commands/eccg.csv'
        }
        call_command('import_org_names', *args, **opts)

        ccgs = PCT.objects.filter(org_type='CCG')
        self.assertEqual(ccgs.count(), 3)
        ccg = PCT.objects.get(code='00C')
        self.assertEqual(ccg.name, 'NHS DARLINGTON CCG')
        address = 'DR PIPER HOUSE, KING STREET, DARLINGTON, COUNTY DURHAM'
        self.assertEqual(ccg.address,
                         address)
        self.assertEqual(ccg.postcode, 'DL3 6JL')
        self.assertEqual(ccg.open_date, datetime.date(2013, 4, 1))
        self.assertEqual(ccg.close_date, None)
