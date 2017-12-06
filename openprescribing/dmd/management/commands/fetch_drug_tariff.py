"""
Fetches Drug Tariff from NHSBSA website, and saves to CSV
"""
from cStringIO import StringIO
from datetime import datetime
from urlparse import urljoin
import io
import logging
import os
import re
import requests
import urllib

from backports import csv
import bs4
import calendar
import pandas as pd

from django.conf import settings
from django.core.management import BaseCommand

from openprescribing.utils import mkdir_p


logger = logging.getLogger(__name__)

FIELDNAMES = ['medicine', 'pack_size', 'unit_of_measure',
              'vmpp', 'tariff_category', 'price_pence']


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
                assert "2000" <= year <= str(datetime.today().year)
            month = month_names.index(month_name.lower())

            year_and_month = '{}_{:02d}'.format(year, month)

            dir_path = os.path.join(
                settings.PIPELINE_DATA_BASEDIR,
                'drug_tariff',
                year_and_month
            )

            if os.path.exists(dir_path):
                continue

            mkdir_p(dir_path)
            xls_url = urljoin(index, a.attrs['href'])
            xls_file = StringIO(requests.get(xls_url).content)
            # drop rows with nulls
            df = pd.read_excel(xls_file, skiprows=2).dropna()
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

            file_name = 'drug_tariff_{}.csv'.format(year_and_month)

            with io.open(
                    os.path.join(dir_path, file_name),
                    'w',
                    encoding='utf8'
            ) as f:
                writer = csv.writer(f)
                writer.writerow(FIELDNAMES)
                for record in df.iterrows():
                    d = record[1]
                    writer.writerow([
                        d['medicine'],
                        d['pack size'],
                        d['unnamed: 2'],
                        int(d['vmpp snomed code']),
                        d['drug tariff category'],
                        int(d['basic price'])
                    ])
