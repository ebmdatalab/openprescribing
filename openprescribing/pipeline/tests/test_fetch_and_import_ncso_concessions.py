# coding=utf8

import contextlib
import datetime
from pathlib import Path

import mock
import pipeline.management.commands.fetch_and_import_ncso_concessions as fetch_ncso
from django.conf import settings
from django.core.management import call_command
from django.test import TestCase
from frontend.models import NCSOConcession
from dmd.models import VMPP


class TestFetchAndImportNCSOConcesions(TestCase):
    fixtures = ["for_ncso_concessions"]

    def test_parse_concessions_from_rss(self):
        base_path = Path(settings.APPS_ROOT) / "pipeline/test-data/pages"
        feed_content = (base_path / "psnc_rss.xml").read_text()
        items = list(fetch_ncso.parse_concessions_from_rss(feed_content))
        expected = [
            {
                "url": "https://mailchi.mp/psnc/march-2023-price-concessions-3rd-update-s6dzuhohv9",
                "date": datetime.date(2023, 3, 1),
                "publish_date": datetime.date(2023, 3, 30),
                "drug": "Bicalutamide 150mg tablets",
                "pack_size": "28",
                "price_pence": 396,
                "supplied_vmpp_id": 1206011000001108,
            },
            {
                "url": "https://mailchi.mp/psnc/march-2023-price-concessions-3rd-update-s6dzuhohv9",
                "date": datetime.date(2023, 3, 1),
                "publish_date": datetime.date(2023, 3, 30),
                "drug": "Cefalexin 250mg tablets",
                "pack_size": "28",
                "price_pence": 286,
                "supplied_vmpp_id": 1053311000001104,
            },
            {
                "url": "https://mailchi.mp/psnc/march-2023-price-concessions-3rd-update-s6dzuhohv9",
                "date": datetime.date(2023, 3, 1),
                "publish_date": datetime.date(2023, 3, 30),
                "drug": "Cinacalcet 30mg tablets",
                "pack_size": "28",
                "price_pence": 1195,
                "supplied_vmpp_id": 8952011000001108,
            },
            {
                "url": "https://mailchi.mp/psnc/march-2023-price-concessions-2nd-update-9lxheenfl0",
                "date": datetime.date(2023, 3, 1),
                "publish_date": datetime.date(2023, 3, 22),
                "drug": "Tranexamic acid 500mg tablets",
                "pack_size": "60",
                "price_pence": 710,
                "supplied_vmpp_id": 1311711000001109,
            },
            {
                "url": "https://mailchi.mp/psnc/march-2023-price-concessions-2nd-update-9lxheenfl0",
                "date": datetime.date(2023, 3, 1),
                "publish_date": datetime.date(2023, 3, 22),
                "drug": "Zolmitriptan 2.5mg tablets",
                "pack_size": "6",
                "price_pence": 1375,
                "supplied_vmpp_id": 1167111000001109,
            },
        ]
        self.assertEqual(items, expected)

    def test_parse_concessions_from_html_skips_known_unparseable(self):
        results = fetch_ncso.parse_concessions_from_html(
            "<broken-html>",
            url="https://mailchi.mp/cpe/atomoxetine-18mg-capsules-updated-reimbursement-price-for-august-2023",
        )
        self.assertEqual(list(results), [])

    def test_match_concession_vmpp_ids_when_correct(self):
        # The happy case: the supplied VMPP ID, name and pack size all match our data so
        # we accept it as is
        concession = {
            "drug": "Amiloride 5mg tablets",
            "pack_size": "28",
            "supplied_vmpp_id": 1191111000001100,
        }
        vmpp_id_to_name = {
            1191111000001100: "Amiloride 5mg tablets 28 tablet",
        }
        expected = {
            "drug": "Amiloride 5mg tablets",
            "pack_size": "28",
            "supplied_vmpp_id": 1191111000001100,
            "vmpp_id": 1191111000001100,
            "vmpp_name": "Amiloride 5mg tablets 28 tablet",
            "supplied_vmpp_name": "Amiloride 5mg tablets 28 tablet",
        }
        self.assertEqual(
            fetch_ncso.match_concession_vmpp_ids([concession], vmpp_id_to_name),
            [expected],
        )

    def test_match_concession_vmpp_ids_when_incorrect(self):
        # Here the pack size associated with the supplied VMPP doesn't match our data,
        # but there's a different VMPP which unambiguously matches, so we use that
        # insted.
        concession = {
            "drug": "Amiloride 5mg tablets",
            "pack_size": "100",
            "supplied_vmpp_id": 1191111000001100,
        }
        vmpp_id_to_name = {
            1191111000001100: "Amiloride 5mg tablets 28 tablet",
            1092811000001107: "Amiloride 5mg tablets 100 tablet",
        }
        expected = {
            "drug": "Amiloride 5mg tablets",
            "pack_size": "100",
            "supplied_vmpp_id": 1191111000001100,
            "vmpp_id": 1092811000001107,
            "vmpp_name": "Amiloride 5mg tablets 100 tablet",
            "supplied_vmpp_name": "Amiloride 5mg tablets 28 tablet",
        }
        self.assertEqual(
            fetch_ncso.match_concession_vmpp_ids([concession], vmpp_id_to_name),
            [expected],
        )

    def test_match_concession_vmpp_ids_when_ambiguous(self):
        # Here the supplied VMPP doesn't match our data and, although we have VMPPs that
        # do match, we don't have a single unambiguous match so we refuse to match any.
        concession = {
            "drug": "Bevacizumab 1.25mg/0.05ml solution for injection vials",
            "pack_size": "1",
            "supplied_vmpp_id": 1000000000000000,
        }
        vmpp_id_to_name = {
            19680811000001105: "Bevacizumab 1.25mg/0.05ml solution for injection vials 1 ml",
            19812211000001101: "Bevacizumab 1.25mg/0.05ml solution for injection vials 1 vial",
        }
        expected = {
            "drug": "Bevacizumab 1.25mg/0.05ml solution for injection vials",
            "pack_size": "1",
            "supplied_vmpp_id": 1000000000000000,
            "vmpp_id": None,
            "vmpp_name": None,
            "supplied_vmpp_name": None,
        }
        self.assertEqual(
            fetch_ncso.match_concession_vmpp_ids([concession], vmpp_id_to_name),
            [expected],
        )

    def test_match_concession_vmpp_ids_using_previous_concession(self):
        concession = {
            "drug": "Amilorde 5mg tablets",  # typo is deliberate
            "pack_size": "28",
            "supplied_vmpp_id": 1000000000000000,
        }
        vmpp_id_to_name = {
            1191111000001100: "Amiloride 5mg tablets 28 tablet",
        }
        # Create previous, manually reconciled concession using the typoed name
        NCSOConcession.objects.create(
            date="2017-10-01",
            drug="Amilorde 5mg tablets",
            pack_size="28",
            price_pence=925,
            vmpp_id=1191111000001100,
        )
        expected = {
            "drug": "Amilorde 5mg tablets",
            "pack_size": "28",
            "supplied_vmpp_id": 1000000000000000,
            "vmpp_id": 1191111000001100,
            "vmpp_name": "Amiloride 5mg tablets 28 tablet",
            "supplied_vmpp_name": None,
        }
        self.assertEqual(
            fetch_ncso.match_concession_vmpp_ids([concession], vmpp_id_to_name),
            [expected],
        )

    def test_fetch_and_import_ncso_concessions(self):
        matched = [
            {
                "date": datetime.date(2023, 3, 1),
                "drug": "Amiloride 5mg tablets",
                "pack_size": "28",
                "price_pence": 925,
                "supplied_vmpp_id": 1191111000001100,
                "vmpp_id": 1191111000001100,
                "vmpp_name": "Amiloride 5mg tablets 28 tablet",
                "supplied_vmpp_name": "Amiloride 5mg tablets 28 tablet",
                "publish_date": datetime.date(2023, 3, 30),
                "url": "https://example.com",
            },
            {
                "date": datetime.date(2023, 3, 1),
                "drug": "Duloxetine 40mg gastro-resistant capsules",
                "pack_size": "56",
                "price_pence": 396,
                "supplied_vmpp_id": 9039011000001105,
                "vmpp_id": 8049011000001108,
                "vmpp_name": "Duloxetine 40mg gastro-resistant capsules 56 capsule",
                "supplied_vmpp_name": "Duloxetine 60mg gastro-resistant capsules 28 capsule",
                "publish_date": datetime.date(2023, 3, 30),
                "url": "https://example.com",
            },
            {
                "date": datetime.date(2023, 3, 1),
                "drug": "Bicalutamide 150mg tablets",
                "pack_size": "28",
                "price_pence": 450,
                "supplied_vmpp_id": 1206011000001108,
                "vmpp_id": None,
                "vmpp_name": None,
                "supplied_vmpp_name": None,
                "publish_date": datetime.date(2023, 3, 30),
                "url": "https://example.com",
            },
        ]

        # Create existing concession which we expect to be updated
        NCSOConcession.objects.create(
            date="2023-03-01",
            drug="Duloxetine 40mg gastro-resistant capsules",
            pack_size="56",
            price_pence=350,
            vmpp_id=8049011000001108,
        )

        with ContextStack(mock.patch.object) as patch:
            patch(fetch_ncso, "requests")
            patch(fetch_ncso, "parse_concessions_from_rss")
            patch(fetch_ncso, "match_concession_vmpp_ids", return_value=matched)

            Client = patch(fetch_ncso, "Client")
            notify_slack = patch(fetch_ncso, "notify_slack")

            call_command("fetch_and_import_ncso_concessions")

            self.assertEqual(NCSOConcession, Client().upload_model.call_args[0][0])
            self.assertIn(
                "Fetched 3 concessions. Imported 2 new concessions.",
                notify_slack.call_args[0][0],
            )

        # Check that all three concessions now exist in the database
        for item in matched:
            self.assertTrue(
                NCSOConcession.objects.filter(
                    date=item["date"],
                    drug=item["drug"],
                    pack_size=item["pack_size"],
                    price_pence=item["price_pence"],
                    vmpp_id=item["vmpp_id"],
                ).exists()
            )

    def test_format_message_when_nothing_to_do(self):
        msg = fetch_ncso.format_message([])
        self.assertEqual(
            msg, "Fetched 0 concessions. Found no new concessions to import."
        )

    def test_fetch_and_import_ncso_concessions_with_corrections(self):
        matched = [
            {
                "date": datetime.date(2023, 4, 1),
                "drug": "Amiloride 5mg tablets",
                "pack_size": "28",
                "price_pence": 925,
                "supplied_vmpp_id": 1191111000001100,
                "vmpp_id": 1191111000001100,
                "vmpp_name": "Amiloride 5mg tablets 28 tablet",
                "supplied_vmpp_name": "Amiloride 5mg tablets 28 tablet",
                "publish_date": datetime.date(2023, 4, 30),
                "url": "https://example.com",
            },
        ]

        # We need a VMPP object corresponding to the correction we're going to insert,
        # but we don't want to have to create the whole graph of related objects so we
        # just copy an existing fixture and give it a new name and ID
        vmpp = VMPP.objects.get(id=1191111000001100)
        vmpp.id = 1240211000001107
        vmpp.nm = "Chlorphenamine 2mg/5ml oral solution 150 ml"
        vmpp.save()

        with ContextStack(mock.patch.object) as patch:
            patch(fetch_ncso, "requests")
            patch(fetch_ncso, "parse_concessions_from_rss")
            patch(fetch_ncso, "match_concession_vmpp_ids", return_value=matched)

            Client = patch(fetch_ncso, "Client")
            notify_slack = patch(fetch_ncso, "notify_slack")

            call_command("fetch_and_import_ncso_concessions")

            self.assertEqual(NCSOConcession, Client().upload_model.call_args[0][0])
            self.assertIn(
                "Fetched 2 concessions. Imported 2 new concessions.",
                notify_slack.call_args[0][0],
            )

        # Check that the explicitly supplied concession and the manual correction now
        # exist in the database
        self.assertTrue(
            NCSOConcession.objects.filter(vmpp_id=1191111000001100).exists()
        )
        self.assertTrue(
            NCSOConcession.objects.filter(vmpp_id=1240211000001107).exists()
        )

    def test_regularise_name(self):
        self.assertEqual(
            fetch_ncso.regularise_name(" * Some Drug Name 500 mg"), "some drug name 500"
        )

    def test_insert_or_update_withdrawn_concession(self):
        vmpp_id = 8049011000001108
        date = datetime.date(2023, 3, 1)

        # Create existing concession which we expect to be deleted
        NCSOConcession.objects.create(
            vmpp_id=vmpp_id,
            date=date,
            drug="Duloxetine 40mg gastro-resistant capsules",
            pack_size="56",
            price_pence=350,
        )

        items = [
            {
                "date": date,
                "vmpp_id": vmpp_id,
                # Mark concession as withdrawn
                "price_pence": fetch_ncso.WITHDRAWN,
                "drug": "Duloxetine 40mg gastro-resistant capsules",
                "pack_size": "56",
                "vmpp_name": "Duloxetine 40mg gastro-resistant capsules 56 capsule",
                "supplied_vmpp_id": vmpp_id,
                "supplied_vmpp_name": "Duloxetine 60mg gastro-resistant capsules 28 capsule",
                "publish_date": datetime.date(2023, 3, 30),
                "url": "https://example.com",
            },
        ]

        fetch_ncso.insert_or_update(items)

        self.assertFalse(
            NCSOConcession.objects.filter(vmpp_id=vmpp_id, date=date).exists()
        )


class ContextStack(contextlib.ExitStack):
    """
    Apply multiple context managers without either nesting or using the hideous multi
    argument form
    """

    def __init__(self, context_manager):
        super().__init__()
        self._context_manager = context_manager

    def __call__(self, *args, **kwargs):
        return self.enter_context(self._context_manager(*args, **kwargs))
