# coding=utf8

from mock import patch

from django.core.management import call_command
from django.db import connection
from django.test import TestCase

from dmd.models import DMDProduct, DMDVmpp, TariffPrice


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

    def assertQuery(self, sql, exp_value):
        with connection.cursor() as cursor:
            cursor.execute(sql)
            row = cursor.fetchone()
            self.assertEqual(row[0], exp_value)
