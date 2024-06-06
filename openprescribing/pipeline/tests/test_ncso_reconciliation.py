from django.core.management import CommandError, call_command
from django.test import TestCase
from frontend.models import NCSOConcession
from mock import patch


class TestNCSOReconciliation(TestCase):
    fixtures = ["for_ncso_concessions"]

    def test_reconcile_ncso_concession(self):
        concession = NCSOConcession.objects.create(
            id=1234,
            date="2017-10-01",
            drug="Amiloride 5mg tablets",
            pack_size="28",
            price_pence=925,
            vmpp_id=None,
        )

        call_command("reconcile_ncso_concession", 1234, 1191111000001100)
        concession.refresh_from_db()
        self.assertEqual(concession.vmpp_id, 1191111000001100)

        with self.assertRaises(CommandError):
            call_command("reconcile_ncso_concession", 9234, 1191111000001100)

        with self.assertRaises(CommandError):
            call_command("reconcile_ncso_concession", 1234, 9191111000001100)

    def test_reconcile_ncso_concession_with_previous_match(self):
        concession_1 = NCSOConcession.objects.create(
            id=1234,
            date="2017-10-01",
            drug="Amiloride 5mg tablets",
            pack_size="28",
            price_pence=925,
            vmpp_id=1191111000001100,
        )
        concession_2 = NCSOConcession.objects.create(
            id=1235,
            date="2017-10-01",
            drug="Amiloride 5mg tablets",
            pack_size="Twenty Eight",
            price_pence=950,
            vmpp_id=None,
        )

        call_command("reconcile_ncso_concession", 1235, 1191111000001100)
        concession_1.refresh_from_db()
        self.assertEqual(concession_1.price_pence, 950)
        self.assertEqual(NCSOConcession.objects.filter(id=concession_2.id).count(), 0)

    def test_reconcile_ncso_concessions(self):
        concession = NCSOConcession.objects.create(
            date="2017-01-01",
            drug="Duloxetine 40mg capsules",
            pack_size="56",
            price_pence=600,
            vmpp_id=None,
        )

        with patch("openprescribing.utils.get_input") as get_input:
            get_input.side_effect = ["dulox", "1", "y"]
            call_command("reconcile_ncso_concessions")

        concession.refresh_from_db()
        self.assertEqual(concession.vmpp_id, 8049011000001108)
