# coding=utf8

import os
from mock import call, patch

import bs4

from django.conf import settings
from django.core.management import call_command
from django.db import connection
from django.test import TestCase

from dmd.models import DMDProduct, DMDVmpp, NCSOConcession, TariffPrice


class CommandsTestCase(TestCase):

    def test_import_dmd(self):
        # These products are created by import_ppu_savings.py, and we want to
        # ensure they are not deleted.
        DMDProduct.objects.get_or_create(
            dmdid=10000000000,
            bnf_code='0601060D0AAA0A0',
            vpid=10000000000,
            name='Glucose Blood Testing Reagents',
            concept_class=1,
            product_type=1
        )
        DMDProduct.objects.get_or_create(
            dmdid=10000000001,
            vpid=10000000001,
            bnf_code='0601060U0AAA0A0',
            name='Urine Testing Reagents',
            product_type=1,
            concept_class=1)

        # dmd.zip doesn't exist!  The data to be imported is already unzipped
        # in dmd/tests/fixtures/dmd/1/.
        path = 'dmd/tests/fixtures/dmd/1/dmd.zip'
        with patch('zipfile.ZipFile'):
            call_command('import_dmd', '--zip_path', path)

        self.assertEqual(DMDProduct.objects.count(), 8)

        self.assertTrue(DMDProduct.objects.filter(dmdid=10000000000).exists())
        self.assertTrue(DMDProduct.objects.filter(dmdid=10000000001).exists())

        diclofenac_prods = DMDProduct.objects.filter(vpid=22480211000001104)
        self.assertEqual(diclofenac_prods.count(), 4)

        vmp = diclofenac_prods.get(concept_class=1)
        self.assertEqual(vmp.dmdid, vmp.vpid)
        self.assertEqual(vmp.name, 'Diclofenac 2.32% gel')

        amps = diclofenac_prods.filter(concept_class=2)
        self.assertEqual(amps.count(), 3)

        amp = amps.get(dmdid=22479611000001102)
        self.assertEqual(amp.name, 'Voltarol 12 Hour Emulgel P 2.32% gel')

        self.assertEqual(
            amp.prescribability.desc, 'Valid as a prescribable product')
        self.assertEqual(
            amp.vmp_non_availability.desc, 'Actual Products Available')
        self.assertEqual(
            amp.controlled_drug_category.desc, 'No Controlled Drug Status')
        self.assertEqual(
            vmp.tariff_category.desc, 'Part VIIIA Category C')

        # A random selection of other tables for which we don't have
        # models.  We don't actively use these (hence no models) but
        # they are sometimes handy for ad-hoc queries.  We consider a
        # random selection to suffice as we'd normally expect to see
        # errors early in the import process if there were problems.

        # From v_vpm2_XXX.xml
        self.assertQuery(
            'SELECT isid FROM dmd_vpi WHERE vpid = 22480211000001104',
            426714006
        )

        # From f_vmpp2_XXX.xml
        self.assertQuery(
            'SELECT pay_catcd FROM dmd_dtinfo WHERE vppid = 22479411000001100',
            3
        )

        # From f_amp2_XXX.xml
        self.assertQuery(
            'SELECT isid FROM dmd_ap_ing WHERE apid = 22479611000001102',
             255859001
        )

        # From f_ampp2_XXX.xml
        self.assertQuery(
            'SELECT price FROM dmd_price_info WHERE appid = 22479711000001106',
            659
        )

        # From f_vmpp2_XXX.xml
        self.assertQuery(
            'SELECT pay_catcd FROM dmd_dtinfo WHERE vppid = 22479411000001100',
            3
        )

        # From f_gtin2_XXX.xml
        self.assertQuery(
            'SELECT gtin FROM dmd_gtin WHERE appid = 22479711000001106',
            '5051562030603'
        )

        # From f_ingredient2_XXX.xml
        self.assertQuery(
            'SELECT nm FROM dmd_ing WHERE isid = 426714006',
            'Diclofenac diethylammonium'
        )

        # From f_lookup2_XXX.xml
        self.assertQuery(
            'SELECT "desc" FROM dmd_lookup_combination_pack_ind WHERE cd = 1',
            'Combination pack'
        )

        # From f_vtm2_XXX.xml
        self.assertQuery(
            'SELECT nm FROM dmd_vtm WHERE vtmid = 32889211000001103',
            'Diclofenac diethylammonium'
        )

        # Now create a TariffPrice object referencing a product whose VPID will
        # change in the next import.

        vmpp = DMDVmpp.objects.get(pk=22479411000001100)
        product = DMDProduct.objects.get(dmdid=vmpp.vpid)

        tp = TariffPrice.objects.create(
            date='2018-07-01',
            vmpp=vmpp,
            product=product,
            tariff_category=product.tariff_category,
            price_pence=100,
        )

        # Import another data dump.  This data is identical to that in dmd/1,
        # except that the VMP with VPID 22480211000001104 has been updated with
        # a new VPID (12345).  This VMP now has a VPIDPREV field, and all
        # references to the old VPID have been updated to the new VPID.

        path = 'dmd/tests/fixtures/dmd/2/dmd.zip'
        with patch('zipfile.ZipFile'):
            call_command('import_dmd', '--zip_path', path)

        # Check that there is no DMDProduct or VMP with the old VPID.
        self.assertFalse(DMDProduct.objects.filter(dmdid=22480211000001104).exists())
        self.assertQuery(
            'SELECT count(*) FROM dmd_vmp WHERE vpid = 22480211000001104',
            0
        )

        # Check that the TariffPrice has been updated to reference a new
        # DMDProduct.
        tp.refresh_from_db()
        self.assertEqual(tp.product_id, 12345)

        # Check that the VMPP has been updated to reference the new VMP.  (No
        # special code is required to update references to VMPs whose VPID has
        # been changed, but we may as well check here anyway.)
        self.assertQuery(
            'SELECT vpid FROM dmd_vmpp WHERE vppid = 22479411000001100',
            12345
        )

    def test_import_dmd_snomed(self):
        path = 'dmd/tests/fixtures/dmd/1/dmd.zip'
        with patch('zipfile.ZipFile'):
            call_command('import_dmd', '--zip_path', path)

        path = 'dmd/tests/fixtures/snomed-mapping/june-2018-snomed-mapping.xlsx'
        call_command('import_dmd_snomed', '--filename', path)

        diclofenac_prods = DMDProduct.objects.filter(vpid=22480211000001104)

        vmp = diclofenac_prods.get(concept_class=1)
        self.assertEqual(vmp.bnf_code, '1003020U0AAAIAI')

        amps = diclofenac_prods.filter(concept_class=2)

        volterol_amp = amps.get(name__contains='Voltarol')
        self.assertEqual(volterol_amp.bnf_code, '1003020U0BBADAI')

        non_volterol_amp = amps.exclude(name__contains='Voltarol').first()
        self.assertEqual(non_volterol_amp.bnf_code, '1003020U0AAAIAI')

    def test_fetch_and_import_ncso_concessions(self):
        # We "download" the following concessions:
        #  2017_11 (current)
        #   * Amiloride (new-and-matched)
        #   * Amlodipine (new-and-unmatched)
        #  2017_10 (archive)
        #   * Amiloride (unchanged, but originally had a typo)
        #   * Anastrozole (unchanged)

        vmpp1 = DMDVmpp.objects.create(
            vppid=1191111000001100,
            nm='Amiloride 5mg tablets 28 tablet',
        )
        vmpp2 = DMDVmpp.objects.create(
            vppid=975211000001100,
            nm='Anastrozole 1mg tablets 28 tablet',
        )

        NCSOConcession.objects.create(
            date='2017-10-01',
            drug='Amilorde 5mg tablets',  # typo is deliberate
            pack_size='28',
            price_concession_pence=925,
            vmpp_id=vmpp1.vppid,
        )
        NCSOConcession.objects.create(
            date='2017-10-01',
            drug='Anastrozole 1mg tablets',
            pack_size='28',
            price_concession_pence=1445,
            vmpp_id=vmpp2.vppid,
        )

        self.assertEqual(NCSOConcession.objects.count(), 2)

        base_path = os.path.join(settings.APPS_ROOT, 'dmd', 'tests', 'pages')

        with open(os.path.join(base_path, 'ncso-archive.html')) as f:
            archive_doc = bs4.BeautifulSoup(f.read(), 'html.parser')

        with open(os.path.join(base_path, 'ncso-current.html')) as f:
            current_doc = bs4.BeautifulSoup(f.read(), 'html.parser')

        patch_path = 'dmd.management.commands.fetch_and_import_ncso_concessions'
        with patch(patch_path + '.Command.download_archive') as download_archive,\
                patch(patch_path + '.Command.download_current') as download_current,\
                patch(patch_path + '.notify_slack') as notify_slack:
            download_archive.return_value = archive_doc
            download_current.return_value = current_doc

            call_command('fetch_and_import_ncso_concessions')

            exp_msg = '\n'.join([
                'Imported 2 new concessions',
                'There are 1 unmatched concessions',
            ])
            self.assertEqual(notify_slack.call_args[0], (exp_msg,))

        self.assertEqual(NCSOConcession.objects.count(), 4)

        for date, drug, pack_size, pcp, vmpp in [
            ['2017-10-01', 'Amiloride 5mg tablets', '28', 925, vmpp1],
            ['2017-10-01', 'Anastrozole 1mg tablets', '28', 1445, vmpp2],
            ['2017-11-01', 'Amiloride 5mg tablets', '28', 925, vmpp1],
            ['2017-11-01', 'Amlodipine 5mg tablets', '28', 375, None],
        ]:
            concession = NCSOConcession.objects.get(
                date=date,
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
            date='2017-01-01',
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

    def assertQuery(self, sql, exp_value):
        with connection.cursor() as cursor:
            cursor.execute(sql)
            row = cursor.fetchone()
            self.assertEqual(row[0], exp_value)
