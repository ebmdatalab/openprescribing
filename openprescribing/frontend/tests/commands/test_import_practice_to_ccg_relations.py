from django.core.management import call_command
from django.test import TestCase
from frontend.models import Practice, PCT, SHA


def setUpModule():
        Practice.objects.create(code='A81043',
                                name='THE MANOR HOUSE SURGERY')
        Practice.objects.create(code='A81044',
                                name='MCKENZIE HOUSE SURGERY')
        Practice.objects.create(code='Y02229',
                                name='MCKENZIE HOUSE SURGERY')
        PCT.objects.create(code='00M', name='SOUTHPORT AND FORMBY CCG')
        PCT.objects.create(code='00K', name='SOUTH MANCHESTER CCG')
        SHA.objects.create(code='Q74', name='TEST AREA TEAM')

def tearDownModule():
    call_command('flush', verbosity=0, interactive=False)


class CommandsTestCase(TestCase):
    def test_import_bnf_codes(self):

        args = []
        fname = 'frontend/tests/fixtures/commands/'
        fname += 'epraccur_sample.csv'
        opts = {
            'filename': fname
        }
        call_command('import_practice_to_ccg_relations', *args, **opts)

        p = Practice.objects.get(code='A81043')
        self.assertEqual(p.ccg.code, '00M')

        p = Practice.objects.get(code='A81044')
        self.assertEqual(p.ccg.code, '00K')

        p = Practice.objects.get(code='Y02229')
        self.assertEqual(p.ccg, None)
