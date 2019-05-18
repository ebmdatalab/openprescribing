# coding=utf8

import os

import bs4
from mock import patch

from django.conf import settings
from django.core.management import call_command
from django.test import TestCase

from dmd2.models import VMPP
from frontend.models import NCSOConcession


class TestFetchAndImportNCSOConcesions(TestCase):

    fixtures = ['for_ncso_concessions']

    def test_fetch_and_import_ncso_concessions(self):
        # We "download" the following concessions:
        #  2017_11 (current)
        #   * Amiloride (new-and-matched)
        #   * Amlodipine (new-and-unmatched)
        #  2017_10 (archive)
        #   * Amiloride (unchanged, but originally had a typo)
        #   * Anastrozole (unchanged)

        vmpp1 = VMPP.objects.get(pk=1191111000001100)
        vmpp2 = VMPP.objects.get(pk=975211000001100)

        NCSOConcession.objects.create(
            date='2017-10-01',
            drug='Amilorde 5mg tablets',  # typo is deliberate
            pack_size='28',
            price_pence=925,
            vmpp=vmpp1,
        )
        NCSOConcession.objects.create(
            date='2017-10-01',
            drug='Anastrozole 1mg tablets',
            pack_size='28',
            price_pence=1445,
            vmpp=vmpp2,
        )

        base_path = os.path.join(settings.APPS_ROOT, 'pipeline', 'test-data', 'pages')

        with open(os.path.join(base_path, 'ncso-archive.html')) as f:
            archive_doc = bs4.BeautifulSoup(f.read(), 'html.parser')

        with open(os.path.join(base_path, 'ncso-current.html')) as f:
            current_doc = bs4.BeautifulSoup(f.read(), 'html.parser')

        patch_path = 'pipeline.management.commands.fetch_and_import_ncso_concessions'
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

        for date, drug, pack_size, price_pence, vmpp in [
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
            self.assertEqual(concession.price_pence, price_pence)
            self.assertEqual(concession.vmpp, vmpp)
