from django.core.management import call_command
from django.test import TestCase
from frontend.models import Presentation


class CommandsTestCase(TestCase):

    def test_import_adqs(self):
        Presentation.objects.create(bnf_code='0101010J0AAAAAA',
                                    name='Mag Trisil_Mix')
        Presentation.objects.create(bnf_code='0104020L0AAAPAP',
                                    name='Loperamide HCl_Oral Susp 25mg/5ml')
        Presentation.objects.create(bnf_code='0401010T0AAAEAE',
                                    name='Temazepam_Oral Soln 10mg/5ml S/F')
        Presentation.objects.create(bnf_code='0401010T0AAAMAM',
                                    name='Temazepam_Tab 10mg')
        Presentation.objects.create(bnf_code='0401020K0AAACAC',
                                    name='Diazepam_Inj 5mg/ml 2ml Amp')

        args = []
        opts = {
            'filename': 'frontend/tests/fixtures/commands/adqs.csv'
        }
        call_command('import_adqs', *args, **opts)

        p = Presentation.objects.get(bnf_code='0104020L0AAAPAP')
        self.assertEqual(p.adq, 8)
        self.assertEqual(p.adq_unit, 'mg')
        self.assertEqual(p.active_quantity, 25)
        self.assertEqual(p.percent_of_adq, 25 / 8.0)

        p = Presentation.objects.get(bnf_code='0401010T0AAAEAE')
        self.assertEqual(p.adq, 20)
        self.assertEqual(p.adq_unit, 'mg')
        self.assertEqual(p.active_quantity, 10)
        self.assertEqual(p.percent_of_adq, 10 / 20.0)

        p = Presentation.objects.get(bnf_code='0401020K0AAACAC')
        self.assertEqual(p.adq, None)
        self.assertEqual(p.adq_unit, None)
