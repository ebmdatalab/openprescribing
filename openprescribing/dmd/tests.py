from django.db import connection
from django.core.management import call_command
from django.test import TestCase

from dmd.models import DMDProduct


class CommandsTestCase(TestCase):

    def test_models(self):
        test_source_directory = 'dmd/tests/fixtures/commands/'
        args = ['--source_directory', test_source_directory]
        opts = {}
        call_command('import_dmd', *args, **opts)
        self.assertEqual(DMDProduct.objects.count(), 2)
        vmp = DMDProduct.objects.get(concept_class=1)
        amp = DMDProduct.objects.get(concept_class=2)
        self.assertEqual([str(x) for x in vmp.amps], [str(amp)])
        self.assertEqual(str(amp.vmp), str(vmp))
        self.assertEqual(
            amp.prescribability.desc, 'Valid as a prescribable product')
        self.assertEqual(
            amp.vmp_non_availability.desc, 'Actual Products Available')
        self.assertEqual(
            amp.controlled_drug_category.desc, 'No Controlled Drug Status')
        self.assertEqual(
            vmp.tariff_category.desc, 'Part VIIIA Category A')

    def test_import_dmd(self):
        test_source_directory = 'dmd/tests/fixtures/commands/'
        args = ['--source_directory', test_source_directory]
        opts = {}
        call_command('import_dmd', *args, **opts)

        # DMDProduct
        self.assertEqual(DMDProduct.objects.count(), 2)
        vmp = DMDProduct.objects.get(concept_class=1)
        amp = DMDProduct.objects.get(concept_class=2)
        self.assertEqual(vmp.full_name, 'Verapamil 160mg tablets')
        self.assertEqual(vmp.vpid, 318248001)
        self.assertEqual(vmp.product_type, 1)
        self.assertEqual(amp.vpid, 318248001)
        self.assertEqual(amp.bnf_code, '0206020T0AAAGAG')
        self.assertEqual(
            amp.full_name, 'Verapamil 160mg tablets (A A H Pharmaceuticals Ltd)')
        self.assertEqual(amp.product_type, 3)

        # A random selection of other tables for which we don't have
        # models.  We don't actively use these (hence no models) but
        # they are sometimes handy for ad-hoc queries.  We consider a
        # random selection to suffice as we'd normally expect to see
        # errors early in the import process if there were problems.
        with connection.cursor() as cursor:
            cursor.execute('SELECT apid FROM dmd_ap_info')
            row = cursor.fetchone()
            self.assertEqual(row[0], 574811000001105)

            cursor.execute('SELECT appid FROM dmd_gtin')
            row = cursor.fetchone()
            self.assertEqual(row[0], 1328111000001105)

            cursor.execute('SELECT "desc" FROM dmd_lookup_legal_category')
            row = cursor.fetchone()
            self.assertEqual(row[0], 'GSL')

            cursor.execute('SELECT "desc" FROM dmd_lookup_supplier')
            row = cursor.fetchone()
            self.assertEqual(row[0], 'DDC Ltd')

            cursor.execute('SELECT strnt_nmrtr_val FROM dmd_vpi')
            row = cursor.fetchone()
            self.assertEqual(row[0], 160)
