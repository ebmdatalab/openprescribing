"""
Fetches Drug Tariff from NHSBSA website, and saves to CSV
"""
from cStringIO import StringIO
import datetime
from urlparse import urljoin
import logging
import os
import re
import requests
import urllib

import bs4
import calendar
from openpyxl import load_workbook

from django.core.management import BaseCommand
from django.db import transaction

from gcutils.bigquery import Client
from dmd.models import DMDProduct, DMDVmpp, TariffPrice
from frontend.models import ImportLog
from openprescribing.slack import notify_slack


logger = logging.getLogger(__name__)


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        host = 'https://www.nhsbsa.nhs.uk'
        index = (host +
                 '/pharmacies-gp-practices-and-appliance-contractors/'
                 'drug-tariff/drug-tariff-part-viii/')
        rsp = requests.get(index)
        doc = bs4.BeautifulSoup(rsp.content, 'html.parser')

        month_names = [x.lower() for x in calendar.month_name]

        imported_months = []

        for a in doc.findAll('a', href=re.compile('Part%20VIIIA')):
            # a.attrs['href'] typically has a filename part like
            # Part%20VIIIA%20September%202017.xlsx
            #
            # We split that into ['Part', 'VIIIA', 'September', '2017']
            words = re.split(
                r'[ -]+',
                urllib.unquote(os.path.splitext(
                    os.path.basename(a.attrs['href']))[0]))
            month_name, year = words[-2:]
            if len(year) == 2:
                year = "20" + year
            month = month_names.index(month_name.lower())
            date = datetime.date(int(year), month, 1)

            if ImportLog.objects.filter(
                category='tariff',
                current_at=date
            ).exists():
                continue

            xls_url = urljoin(index, a.attrs['href'])
            xls_file = StringIO(requests.get(xls_url).content)

            import_month(xls_file, date)
            imported_months.append((year, month))

        if imported_months:
            client = Client('dmd')
            client.upload_model(TariffPrice)

            for year, month in imported_months:
                msg = 'Imported Drug Tariff for %s_%s' % (year, month)
                notify_slack(msg)
        else:
            msg = 'Found no new tariff data to import'
            notify_slack(msg)


def import_month(xls_file, date):
    wb = load_workbook(xls_file)
    rows = wb.active.rows

    # The first row is a title, and the second is empty
    next(rows)
    next(rows)

    # The third row is column headings
    header_row = next(rows)
    headers = [(c.value or '?').lower() for c in header_row]
    assert headers == [
        'medicine',
        'pack size',
        '?',
        'vmpp snomed code',
        'drug tariff category',
        'basic price'
    ]

    with transaction.atomic():
        for row in rows:
            values = [c.value for c in row]
            if all(v is None for v in values):
                continue

            d = dict(zip(headers, values))

            TariffPrice.objects.get_or_create(
                date=date,
                vmpp_id=d['vmpp snomed code'],
                product_id=get_product_id(d['vmpp snomed code']),
                tariff_category_id=get_tariff_cat_id(d['drug tariff category']),
                price_pence=int(d['basic price'])
            )

        ImportLog.objects.create(
            category='tariff',
            current_at=date,
            filename='none',
        )


def get_tariff_cat_id(cat):
    if 'Category A' in cat:
        return 1
    elif 'Category C' in cat:
        return 3
    elif 'Category M' in cat:
        return 11
    else:
        assert False, 'Unknown category: {}'.format(cat)


def get_product_id(vmpp):
    try:
        vpid = DMDVmpp.objects.get(pk=vmpp).vpid
    except DMDVmpp.DoesNotExist:
        logger.exception("Could not find VMPP with id %s", vmpp)
        raise

    try:
        product = DMDProduct.objects.get(vpid=vpid, concept_class=1)
    except DMDProduct.DoesNotExist:
        logger.exception("Could not find DMD product with VPID %s", vpid)
        raise

    return product.pk
