# coding=utf8

from mock import patch

from django.db import connection
from django.core.management import call_command
from django.test import TestCase

from dmd.models import DMDProduct, DMDVmpp, NCSOConcession


class CommandsTestCase(TestCase):

    def test_models(self):
        path = 'dmd/tests/fixtures/commands/dmd.zip'
        with patch('zipfile.ZipFile'):
            call_command('import_dmd', '--zip_path', path)

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
        path = 'dmd/tests/fixtures/commands/dmd.zip'
        with patch('zipfile.ZipFile'):
            call_command('import_dmd', '--zip_path', path)

        # DMDProduct
        self.assertEqual(DMDProduct.objects.count(), 2)
        vmp = DMDProduct.objects.get(concept_class=1)
        amp = DMDProduct.objects.get(concept_class=2)
        self.assertEqual(vmp.full_name, 'Verapamil 160mg tablets')
        self.assertEqual(vmp.vpid, 318248001)
        self.assertEqual(vmp.product_type, 1)
        self.assertEqual(amp.vpid, 318248001)
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

    def test_import_dmd_snomed(self):
        path = 'dmd/tests/fixtures/commands/dmd.zip'
        with patch('zipfile.ZipFile'):
            call_command('import_dmd', '--zip_path', path)

        path = 'dmd/tests/fixtures/commands/Converted_DRUG_SNOMED_BNF.xlsx'
        call_command('import_dmd_snomed', '--filename', path)

        amp = DMDProduct.objects.get(concept_class=2)
        self.assertEqual(amp.bnf_code, '0206020T0AAAGAG')

    def test_import_ncso_concessions(self):
        vmpp1 = DMDVmpp.objects.create(
            vppid=1092811000001107,
            nm='Amiloride 5mg tablets 100 tablet',
        )
        vmpp2 = DMDVmpp.objects.create(
            vppid=8049011000001108,
            nm='Duloxetine 40mg gastro-resistant capsules 56 capsule',
        )

        NCSOConcession.objects.create(
            year_and_month='2017_01',
            drug='Duloxetine 40mg capsules',
            pack_size='56',
            price_concession_pence=600,
            vmpp_id=vmpp2.vppid,
        )

        path = 'dmd/tests/fixtures/commands/ncso_concessions_2017_02.csv'
        call_command('import_ncso_concessions', '--filename', path)

        cons1 = NCSOConcession.objects.get(
            year_and_month='2017_02',
            drug='Amiloride 5mg tablets'
        )

        cons2 = NCSOConcession.objects.get(
            year_and_month='2017_02',
            drug='Duloxetine 40mg gastro-resistant capsules'
        )

        cons3 = NCSOConcession.objects.get(
            year_and_month='2017_02',
            drug='Vitamin B Co Strong tablets'
        )

        self.assertEqual(cons1.pack_size, '100')
        self.assertEqual(cons1.price_concession_pence, 925)
        self.assertEqual(cons1.vmpp, vmpp1)

        self.assertEqual(cons2.pack_size, '56')
        self.assertEqual(cons2.price_concession_pence, 725)
        self.assertEqual(cons2.vmpp, vmpp2)

        self.assertEqual(cons3.pack_size, '28')
        self.assertEqual(cons3.price_concession_pence, 525)
        self.assertEqual(cons3.vmpp, None)
