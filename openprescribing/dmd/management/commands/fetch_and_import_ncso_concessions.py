# coding=utf8

import calendar
import datetime
import logging
import re

import bs4
import requests

from django.core.management import BaseCommand

from dmd.models import NCSOConcession, DMDVmpp
from gcutils.bigquery import Client
from openprescribing.slack import notify_slack

logger = logging.getLogger(__file__)


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        self.vmpps = DMDVmpp.objects.values('nm', 'vppid')
        num_before = NCSOConcession.objects.count()
        self.import_from_archive()
        self.import_from_current()
        self.reconcile()
        num_after = NCSOConcession.objects.count()
        num_unmatched = NCSOConcession.objects.filter(vmpp__isnull=True).count()

        Client('dmd').upload_model(NCSOConcession)

        if num_before == num_after:
            msg = 'Found no new concessions to import'
        else:
            msg = 'Imported %s new concessions' % (num_after - num_before)
        if num_unmatched:
            msg += '\nThere are %s unmatched concessions' % num_unmatched
        notify_slack(msg)

    def import_from_archive(self):
        logger.info('import_from_archive')

        doc = self.download_archive()
        for h2 in doc.find_all('h2', class_='trigger'):
            table = h2.find_next('table')
            date = self.date_from_heading(h2)
            drugs_and_pack_sizes = self.import_from_table(table, date)
            self.delete_missing(drugs_and_pack_sizes, date)

    def download_archive(self):
        url = 'http://psnc.org.uk/dispensing-supply/supply-chain/generic-shortages/ncso-archive/'
        rsp = requests.get(url)
        return bs4.BeautifulSoup(rsp.content, 'html.parser')

    def import_from_current(self):
        logger.info('import_from_current')

        doc = self.download_current()

        h1s = doc.find_all('h1', string=re.compile('\w+ \d{4}'))
        assert len(h1s) == 1

        date = self.date_from_heading(h1s[0])

        drugs_and_pack_sizes = set()

        for table in doc.find_all('table'):
            drugs_and_pack_sizes |= self.import_from_table(table, date)

        self.delete_missing(drugs_and_pack_sizes, date)

    def download_current(self):
        url = 'http://psnc.org.uk/dispensing-supply/supply-chain/generic-shortages/'
        rsp = requests.get(url)
        return bs4.BeautifulSoup(rsp.content, 'html.parser')

    def date_from_heading(self, heading):
        month_name, year = heading.text.strip().split()
        month_names = list(calendar.month_name)
        month = month_names.index(month_name)
        return datetime.date(int(year), month, 1)

    def import_from_table(self, table, date):
        '''Creates NCSOConcession objects for any new records in the table.

        Returns set of strings containing drug name and pack size for all
        records in the table.
        '''

        logger.info('import_from_table %s', date)

        if date < datetime.date(2014, 8, 1):
            # Data older than August 2018 is in a different format and we don't
            # need it at the moment.
            return set()

        trs = table.find_all('tr')
        records = [[td.text.strip() for td in tr.find_all('td')] for tr in trs]

        if len(records[0]) != 3:
            # Some tables on a page don't actually list concessions, but
            # there's no obvious way of selecting just the tables with
            # concessions. We can ignore tables that don't have three columns.
            # Non-concession tables with three columns will obviously slip
            # through the net here, but will presumably trigger the asserts
            # below, and we can cross that bridge when the time comes.
            return set()

        # Make sure the first row contains expected headers.
        # Unfortunately, the header names are not consistent.
        assert 'drug' in records[0][0].lower()
        assert 'pack' in records[0][1].lower()
        assert 'price' in records[0][2].lower()

        drugs_and_pack_sizes = set()

        for record in records[1:]:
            drug, pack_size, price_concession = [fix_spaces(item) for item in record]
            drug = drug.replace('(new)', '').strip()
            match = re.search(u'£(\d+)\.(\d\d)', price_concession)
            price_concession_pence = 100 * int(match.groups()[0]) \
                + int(match.groups()[1])
            drug_and_pack_size = u'{} {}'.format(drug, pack_size)
            drugs_and_pack_sizes.add(drug_and_pack_size)

            _, created = NCSOConcession.objects.get_or_create(
                date=date,
                drug=drug,
                pack_size=pack_size,
                price_concession_pence=price_concession_pence,
            )

            if created:
                logger.info('Creating %s %s', drug_and_pack_size, date)

        return drugs_and_pack_sizes

    def delete_missing(self, drugs_and_pack_sizes, date):
        for concession in NCSOConcession.objects.filter(date=date):
            if concession.drug_and_pack_size not in drugs_and_pack_sizes:
                logger.info('Deleting %s %s', concession.drug_and_pack_size, date)
                concession.delete()

    def reconcile(self):
        for concession in NCSOConcession.objects.filter(vmpp_id__isnull=True):
            logger.info('Reconciling %s', concession.drug_and_pack_size)
            matching_vmpp_id = self.get_matching_vmpp_id(concession)
            if matching_vmpp_id is not None:
                concession.vmpp_id = matching_vmpp_id
                concession.save()

    def get_matching_vmpp_id(self, concession):
        previous_concession = NCSOConcession.objects.filter(
            drug=concession.drug,
            pack_size=concession.pack_size,
            vmpp__isnull=False,
        ).exclude(
            date=concession.date
        ).first()

        if previous_concession is not None:
            logger.info('Found previous matching concession')
            return previous_concession.vmpp_id

        ncso_name = regularise_ncso_name(concession.drug_and_pack_size)

        for vmpp in self.vmpps:
            vpmm_name = re.sub(' */ *', '/', vmpp['nm'].lower())

            if vpmm_name == ncso_name or vpmm_name.startswith(ncso_name + ' '):
                logger.info('Found match')
                return vmpp['vppid']

        logger.info('No match found')
        return None


def fix_spaces(s):
    '''Remove extra spaces and convert non-breaking spaces to normal ones.'''

    s = s.replace(u'\xa0', ' ')
    s = s.strip()
    s = re.sub(' +', ' ', s)
    return s


def regularise_ncso_name(name):
    # dm+d uses "microgram" or "micrograms", usually with these rules
    name = name.replace('mcg ', 'microgram ')
    name = name.replace('mcg/', 'micrograms/')

    # dm+d uses "microgram" rather than "0.X.mg"
    name = name.replace('0.5mg', '500microgram')
    name = name.replace('0.25mg', '250microgram')

    # dm+d uses "square cm"
    name = name.replace('sq cm', 'square cm')

    # dm+d records measured in mg/ml have a space before the final "ml"
    # eg: Abacavir 20mg/ml oral solution sugar free 240 ml
    name = re.sub(r'(\d)ml$', r'\1 ml', name)

    # dm+d records have "gram$" not "g$"
    # eg: Estriol 0.01% cream 80 gram
    name = re.sub(r'(\d)g$', r'\1 gram', name)

    # Misc. commont replacements
    name = name.replace('Oral Susp SF', 'oral suspension sugar free')
    name = name.replace('gastro- resistant', 'gastro-resistant')
    name = name.replace('/ml', '/1ml')

    # Lowercase
    name = name.lower()

    # Remove spaces around slashes
    name = re.sub(' */ *', '/', name)

    return name
