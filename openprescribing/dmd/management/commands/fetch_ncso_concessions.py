import calendar
import io
import os

from backports import csv
import bs4
import requests

from django.conf import settings
from django.core.management import BaseCommand

from openprescribing.utils import mkdir_p


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        url = 'http://psnc.org.uk/dispensing-supply/supply-chain/generic-shortages/ncso-archive/'
        rsp = requests.get(url)
        doc = bs4.BeautifulSoup(rsp.content, 'html.parser')

        month_names = list(calendar.month_name)

        for h2 in doc.findAll('h2', class_='trigger'):
            month_name, year = h2.text.strip().split()
            month = month_names.index(month_name)

            year_and_month = '{}_{:02d}'.format(year, month)

            if year_and_month < '2014_08':
                break

            dir_path = os.path.join(
                settings.PIPELINE_DATA_BASEDIR,
                'ncso_concessions',
                year_and_month
            )

            if os.path.exists(dir_path):
                continue

            mkdir_p(dir_path)

            table = h2.findNext('table')

            records = []
            for tr in table.findAll('tr'):
                records.append([td.text for td in tr.findAll('td')])

            # Make sure the first row contains expected headers.
            # Unfortunately, the header names are not consistent.
            assert 'drug' in records[0][0].lower()
            assert 'pack' in records[0][1].lower()
            assert 'price' in records[0][2].lower()

            # Drop header row
            records = records[1:]

            path = os.path.join(
                dir_path,
                'ncso_concessions_{}.csv'.format(year_and_month)
            )

            with io.open(path, 'w', encoding='utf8') as f:
                writer = csv.writer(f)
                for record in records:
                    writer.writerow(record)
