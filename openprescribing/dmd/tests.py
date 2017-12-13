# coding=utf8

import os
from mock import call, patch

import bs4

from django.conf import settings
from django.core.management import call_command
from django.db import connection
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

    def test_fetch_and_import_ncso_concessions(self):
        # We "download" the following concessions:
        #  2017_11 (current)
        #   * Amiloride (new-and-matched)
        #   * Amlodipine (new-and-unmatched)
        #  2017_10 (archive)
        #   * Amiloride (changed)
        #   * Anastrozole (unchanged)

        vmpp1 = DMDVmpp.objects.create(
            vppid=1092811000001107,
            nm='Amiloride 5mg tablets 100 tablet',
        )
        vmpp2 = DMDVmpp.objects.create(
            vppid=975211000001100,
            nm='Anastrozole 1mg tablets 28 tablet',
        )

        NCSOConcession.objects.create(
            year_and_month='2017_10',
            drug='Amiloride 5mg tablets',
            pack_size='28',
            price_concession_pence=925,
            vmpp_id=vmpp1.vppid,
        )
        NCSOConcession.objects.create(
            year_and_month='2017_10',
            drug='Anastrozole 1mg tablets',
            pack_size='28',
            price_concession_pence=1335,
            vmpp_id=vmpp2.vppid,
        )

        self.assertEqual(NCSOConcession.objects.count(), 2)

        base_path = os.path.join(settings.SITE_ROOT, 'dmd', 'tests', 'pages')

        with open(os.path.join(base_path, 'ncso-archive.html')) as f:
            archive_doc = bs4.BeautifulSoup(f.read(), 'html.parser')

        with open(os.path.join(base_path, 'ncso-current.html')) as f:
            current_doc = bs4.BeautifulSoup(f.read(), 'html.parser')

        patch_path = 'dmd.management.commands.fetch_and_import_ncso_concessions'
        with patch(patch_path + '.Command.download_archive') as download_archive,\
                patch(patch_path + '.Command.download_current') as download_current,\
                patch(patch_path + '.logger.info') as info:
            download_archive.return_value = archive_doc
            download_current.return_value = current_doc

            call_command('fetch_and_import_ncso_concessions')

            expected_logging_calls = [
                call('New and matched: %s', 1),
                call('New and unmatched: %s', 1),
                call('Changed: %s', 1),
                call('Unchanged: %s', 1),
            ]
            self.assertEqual(info.call_args_list[-4:], expected_logging_calls)

        self.assertEqual(NCSOConcession.objects.count(), 4)

        for year_and_month, drug, pack_size, pcp, vmpp in [
            ['2017_10', 'Amiloride 5mg tablets', '28', 925, vmpp1],
            ['2017_10', 'Anastrozole 1mg tablets', '28', 1445, vmpp2],
            ['2017_11', 'Amiloride 5mg tablets', '28', 925, vmpp1],
            ['2017_11', 'Amlodipine 5mg tablets', '28', 375, None],
        ]:
            concession = NCSOConcession.objects.get(
                year_and_month=year_and_month,
                drug=drug
            )
            self.assertEqual(concession.pack_size, pack_size)
            self.assertEqual(concession.price_concession_pence, pcp)
            self.assertEqual(concession.vmpp, vmpp)

    def test_reconcile_ncso_concessions(self):
        vmpp = DMDVmpp.objects.create(
            vppid=8049011000001108,
            nm='Duloxetine 40mg gastro-resistant capsules 56 capsule',
        )

        DMDVmpp.objects.create(
            vppid=9039011000001105,
            nm='Duloxetine 60mg gastro-resistant capsules 28 capsule',
        )

        DMDVmpp.objects.create(
            vppid=9039111000001106,
            nm='Duloxetine 60mg gastro-resistant capsules 84 capsule',
        )

        DMDVmpp.objects.create(
            vppid=940711000001101,
            nm='Carbamazepine 200mg tablets 84 tablet',
        )

        concession = NCSOConcession.objects.create(
            year_and_month='2017_01',
            drug='Duloxetine 40mg capsules',
            pack_size='56',
            price_concession_pence=600,
            vmpp_id=None,
        )

        with patch('openprescribing.utils.get_input') as get_input:
            get_input.side_effect = ['dulox', '1', 'y']
            call_command('reconcile_ncso_concessions')

        concession.refresh_from_db()
        self.assertEqual(concession.vmpp, vmpp)
