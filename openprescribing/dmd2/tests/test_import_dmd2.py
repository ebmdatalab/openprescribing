from django.core.management import call_command, CommandError
from django.test import TestCase

from dmd2.models import AMP, AMPP, VMP, VMPP


class TestImportDmd2(TestCase):
    def test_import_dmd2(self):
        # See fixtures/dmd/README.txt for details of what objects will be
        # created.

        # Import the data.
        call_command('import_dmd2', 'dmd2/tests/fixtures/dmd/1/')

        # Check that correct number of objects have been created.
        self.assertEqual(VMP.objects.count(), 2)
        self.assertEqual(VMPP.objects.count(), 5)
        self.assertEqual(AMP.objects.count(), 5)
        self.assertEqual(AMPP.objects.count(), 11)

        # Check that a selection of fields have been set correctly.
        vmp = VMP.objects.get(id=22480211000001104)
        self.assertEqual(vmp.nm, 'Diclofenac 2.32% gel')
        self.assertEqual(vmp.pres_stat.descr, 'Valid as a prescribable product')
        self.assertEqual(vmp.vmpp_set.count(), 3)
        self.assertEqual(vmp.amp_set.count(), 3)

        vmpp = VMPP.objects.get(id=22479511000001101)
        self.assertEqual(vmpp.nm, 'Diclofenac 2.32% gel 30 gram')
        self.assertEqual(vmpp.vmp, vmp)
        self.assertEqual(vmpp.qty_uom.descr, 'gram')
        self.assertEqual(vmpp.ampp_set.count(), 3)

        amp = AMP.objects.get(id=29915211000001103)
        self.assertEqual(amp.nm, 'Diclofenac 2.32% gel')
        self.assertEqual(
            amp.descr,
            'Diclofenac 2.32% gel (Colorama Pharmaceuticals Ltd)'
        )
        self.assertEqual(amp.vmp, vmp)
        self.assertEqual(amp.supp.descr, 'Colorama Pharmaceuticals Ltd')
        self.assertEqual(amp.ampp_set.count(), 2)

        ampp = AMPP.objects.get(id=29915311000001106)
        self.assertEqual(
            ampp.nm,
            'Diclofenac 2.32% gel (Colorama Pharmaceuticals Ltd) 30 gram'
        )
        self.assertEqual(ampp.vmpp, vmpp)
        self.assertEqual(ampp.amp, amp)
        self.assertEqual(ampp.legal_cat.descr, 'P')

        # Import updated data.  This data is identical to that in dmd/1, except
        # that the VMP with VPID 22480211000001104 has been updated with a new
        # VPID (12345).  This VMP now has a VPIDPREV field, and all references
        # to the old VPID have been updated to the new VPID.
        call_command('import_dmd2', 'dmd2/tests/fixtures/dmd/2/')

        # Check that no VMP present with old VPID, that a new VMP has been
        # created, and that references to VMP have been updated.
        self.assertIsNone(VMP.objects.filter(id=22480211000001104).first())
        vmp = VMP.objects.get(id=12345)
        self.assertEqual(vmp.vpidprev, 22480211000001104)

        vmpp.refresh_from_db()
        self.assertEqual(vmpp.vmp, vmp)

        amp.refresh_from_db()
        self.assertEqual(amp.vmp, vmp)
