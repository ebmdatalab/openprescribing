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
import pandas as pd

from django.core.management import BaseCommand
from django.db import transaction

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

        for a in doc.findAll('a', class_='excel', title=re.compile('VIIIA')):
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
                assert "2000" <= year <= str(datetime.date.today().year)
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
            msg = 'Imported Drug Tariff for %s_%s' % (year, month)
            notify_slack(msg)


def import_month(xls_file, date):
    # drop rows with nulls
    df = pd.read_excel(xls_file, skiprows=2)
    df = df.dropna()
    expected_cols = [
        'medicine',
        'pack size',
        'unnamed: 2',
        'vmpp snomed code',
        'drug tariff category',
        'basic price']
    df.columns = [x.lower() for x in df.columns]
    assert [x for x in df.columns] == expected_cols, \
        "%s doesn't match %s" % (df.columns, expected_cols)

    with transaction.atomic():
        for record in df.iterrows():
            d = record[1]
            TariffPrice.objects.get_or_create(
                date=date,
                vmpp_id=d['vmpp snomed code'],
                product_id=get_product_id(d['vmpp snomed code']),
                tariff_category_id=get_tariff_cat_id(d['drug tariff category']),
                price_pence=int(d['basic price'])
            )

        ImportLog.objects.create(
            category='tariff',
            filename=kwargs['filename'],
            current_at=date)


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
    vpid = DMDVmpp.objects.get(pk=vmpp).vpid
    product = DMDProduct.objects.get(vpid=vpid, concept_class=1)
    return product.pk
