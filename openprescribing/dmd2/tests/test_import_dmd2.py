import csv
import shutil
import tempfile

from mock import patch

from django.core.management import call_command, CommandError
from django.test import TestCase

from dmd2.models import AMP, AMPP, VMP, VMPP
from dmd2.management.commands.import_dmd2 import get_common_name
from frontend.models import Presentation, NCSOConcession


class TestImportDmd2(TestCase):
    @classmethod
    def setUpTestData(cls):
        for bnf_code, name in [
            ('0203020C0AAAAAA', 'Adenosine_I/V Inf 3mg/ml 2ml Vl'),
            ('1003020U0AAAIAI', 'Diclofenac Sod_Gel 2.32%'),
            ('1003020U0BBADAI', 'Voltarol 12 Hour Emulgel P_Gel 2.32%'),
            ('1305020C0AAFVFV', 'Coal Tar 10%/Salic Acid 5%/Aq_Crm'),
            ('1106000X0AAAIAI', 'Piloc HCl_Eye Dps 6%'),
            ('090402000BBHCA0', 'Nutrison Pack_Stnd'),
        ]:
            Presentation.objects.create(bnf_code=bnf_code, name=name)

        cls.logs_path = tempfile.mkdtemp()

        # Import the data.  See dmd2/tests/data/README.txt for details of what
        # objects will be created.
        with patch('gcutils.bigquery.Client.upload_model'):
            call_command(
                'import_dmd2',
                'dmd2/tests/data/dmd/1/',
                'dmd2/tests/data/bnf_code_mapping/mapping.xlsx',
                cls.logs_path + '/1',
            )

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.logs_path)
        super(TestImportDmd2, cls).tearDownClass()

    def test_objects_created(self):
        # Check that correct number of objects have been created.
        self.assertEqual(VMP.objects.count(), 7)
        self.assertEqual(VMPP.objects.count(), 14)
        self.assertEqual(AMP.objects.count(), 15)
        self.assertEqual(AMPP.objects.count(), 26)

        # Check that a selection of fields have been set correctly.
        vmp = VMP.objects.get(id=22480211000001104)
        self.assertEqual(vmp.nm, 'Diclofenac 2.32% gel')
        self.assertEqual(vmp.pres_stat.descr, 'Valid as a prescribable product')
        self.assertEqual(vmp.vmpp_set.count(), 3)
        self.assertEqual(vmp.amp_set.count(), 3)
        self.assertEqual(vmp.bnf_code, '1003020U0AAAIAI')

        vmpp = VMPP.objects.get(id=22479511000001101)
        self.assertEqual(vmpp.nm, 'Diclofenac 2.32% gel 30 gram')
        self.assertEqual(vmpp.vmp, vmp)
        self.assertEqual(vmpp.qty_uom.descr, 'gram')
        self.assertEqual(vmpp.ampp_set.count(), 3)
        self.assertEqual(vmpp.bnf_code, '1003020U0AAAIAI')

        amp = AMP.objects.get(id=29915211000001103)
        self.assertEqual(amp.nm, 'Diclofenac 2.32% gel')
        self.assertEqual(
            amp.descr, 'Diclofenac 2.32% gel (Colorama Pharmaceuticals Ltd)'
        )
        self.assertEqual(amp.vmp, vmp)
        self.assertEqual(amp.supp.descr, 'Colorama Pharmaceuticals Ltd')
        self.assertEqual(amp.ampp_set.count(), 2)
        self.assertIsNone(amp.bnf_code)

        ampp = AMPP.objects.get(id=29915311000001106)
        self.assertEqual(
            ampp.nm, 'Diclofenac 2.32% gel (Colorama Pharmaceuticals Ltd) 30 gram'
        )
        self.assertEqual(ampp.vmpp, vmpp)
        self.assertEqual(ampp.amp, amp)
        self.assertEqual(ampp.legal_cat.descr, 'P')
        self.assertIsNone(amp.bnf_code)

        # The following AMP and AMPP do have BNF codes.
        self.assertEqual(
            AMP.objects.get(id=22479611000001102).bnf_code, '1003020U0BBADAI'
        )
        self.assertEqual(
            AMPP.objects.get(id=22479911000001108).bnf_code, '1003020U0BBADAI'
        )

    def test_vmp_bnf_codes_set(self):
        # This VMP does not have a BNF code in the mapping, but all its VMPPs
        # have the same BNF code, so we assign this to the VMP.
        self.assertEqual(
            VMP.objects.get(id=35894711000001106).bnf_code, '0203020C0AAAAAA'
        )

    def test_dmd_names(self):
        def _assert_dmd_name(bnf_code, exp_dmd_name):
            self.assertEqual(
                Presentation.objects.get(bnf_code=bnf_code).dmd_name, exp_dmd_name
            )

        # This BNF code corresponds to a single VMP.
        _assert_dmd_name('1003020U0AAAIAI', 'Diclofenac 2.32% gel')

        # This BNF code corresponds to a single AMP.
        _assert_dmd_name('1003020U0BBADAI', 'Voltarol 12 Hour Emulgel P 2.32% gel')

        # This BNF code corresponds to multiple VMPs and a common name can be
        # inferred.
        _assert_dmd_name('1106000X0AAAIAI', 'Pilocarpine hydrochloride 6% eye drops')

        # This BNF code corresponds to multiple VMPs and a common name cannot
        # be inferred.
        _assert_dmd_name('1305020C0AAFVFV', None)

        # This BNF code corresponds to multiple AMPPs and a common name can be
        # inferred.
        _assert_dmd_name('090402000BBHCA0', 'Nutrison liquid (Nutricia Ltd)')

    def test_logs(self):
        with open(self.logs_path + '/1/summary.csv') as f:
            summary = list(csv.reader(f))

        exp_summary = [
            ['VMP', '7'],
            ['AMP', '15'],
            ['VMPP', '14'],
            ['AMPP', '26'],
            ['dmd-objs-present-in-mapping-only', '0'],
            ['vmps-with-inferred-bnf-code', '2'],
            ['vmps-with-no-bnf-code', '1'],
            ['bnf-codes-with-multiple-dmd-objs', '3'],
            ['bnf-codes-with-multiple-dmd-objs-and-no-inferred-name', '1'],
            ['vmpps-with-different-bnf-code-to-vmp', '0'],
            ['ampps-with-different-bnf-code-to-amp', '3'],
        ]

        self.assertEqual(summary, exp_summary)

    def test_another_import(self):
        # Import updated data.  This data is identical to that in dmd/1, except
        # that the VMP with VPID 22480211000001104 has been updated with a new
        # VPID (12345).  This VMP now has a VPIDPREV field, and all references
        # to the old VPID have been updated to the new VPID.
        #
        # Additionally, there is now an NCSOConcession with a FK reference to
        # an existing VMPP.

        vmpp = VMPP.objects.get(id=22479511000001101)
        concession = NCSOConcession.objects.create(
            date='2019-06-01',
            vmpp=vmpp,
            drug=vmpp.nm,
            pack_size=vmpp.qtyval,
            price_pence=123
        )

        vmpp.delete()

        with patch('gcutils.bigquery.Client.upload_model'):
            call_command(
                'import_dmd2',
                'dmd2/tests/data/dmd/2/',
                'dmd2/tests/data/bnf_code_mapping/mapping.xlsx',
                self.logs_path + '/2',
            )

        # Check that no VMP present with old VPID, that a new VMP has been
        # created, and that references to VMP have been updated.
        self.assertIsNone(VMP.objects.filter(id=22480211000001104).first())
        vmp = VMP.objects.get(id=12345)
        self.assertEqual(vmp.vpidprev, 22480211000001104)

        vmpp = VMPP.objects.get(id=22479511000001101)
        self.assertEqual(vmpp.vmp, vmp)

        amp = AMP.objects.get(id=29915211000001103)
        self.assertEqual(amp.vmp, vmp)

        concession.refresh_from_db()
        self.assertEqual(concession.vmpp, vmpp)


class TestGetCommonName(TestCase):
    def test_common_name(self):
        self._test_get_common_name(
            [
                'Zoledronic acid 4mg/100ml infusion bags',
                'Zoledronic acid 4mg/100ml infusion bottles',
            ],
            'Zoledronic acid 4mg/100ml infusion',
        )

    def test_no_common_name(self):
        self._test_get_common_name(
            ["Lassar's paste", 'Zinc and Salicylic acid paste'], None
        )

    def test_common_name_too_short(self):
        self._test_get_common_name(
            [
                'Coal tar 10% / Salicylic acid 5% in Aqueous cream',
                'Coal tar solution 10% / Salicylic acid 5% in Aqueous cream',
            ],
            None,
        )

    def test_trailing_with_removed(self):
        self._test_get_common_name(
            [
                'Polyfield Soft Vinyl Patient Pack with small gloves',
                'Polyfield Soft Vinyl Patient Pack with medium gloves',
                'Polyfield Soft Vinyl Patient Pack with large gloves',
            ],
            'Polyfield Soft Vinyl Patient Pack',
        )

    def test_trailing_oral_removed(self):
        self._test_get_common_name(
            [
                'Acetazolamide 350mg/5ml oral solution',
                'Acetazolamide 350mg/5ml oral suspension',
            ],
            'Acetazolamide 350mg/5ml',
        )

    def _test_get_common_name(self, names, exp_common_name):
        self.assertEqual(get_common_name(names), exp_common_name)
