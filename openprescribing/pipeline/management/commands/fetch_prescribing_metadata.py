import datetime
import os

import requests

from django.conf import settings
from django.core.management import BaseCommand, CommandError

from openprescribing.utils import mkdir_p


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('dataset', choices=['addresses', 'chemicals'])

    def handle(self, *args, **kwargs):
        today = datetime.date.today()
        year = today.year
        month = today.month

        num_missing_months = 0
        filename_fragment = {
            'addresses': 'ADDR+BNFT',
            'chemicals': 'CHEM+SUBS',
        }[kwargs['dataset']]

        while True:
            date = datetime.date(year, month, 1)
            year_and_month = date.strftime('%Y_%m')  # eg 2017_01

            dir_path = os.path.join(
                settings.PIPELINE_DATA_BASEDIR,
                'prescribing_metadata',
                year_and_month
            )
            filename = date.strftime('T%Y%m{}.CSV').format(filename_fragment)
            file_path = os.path.join(dir_path, filename)

            if os.path.exists(file_path):
                break

            mkdir_p(dir_path)

            # eg http://datagov.ic.nhs.uk/presentation/2017_08_August/T201708ADDR+BNFT.CSV
            base_url = 'http://datagov.ic.nhs.uk/presentation'
            path_fragment = date.strftime('%Y_%m_%B')
            url = '{}/{}/{}'.format(base_url, path_fragment, filename)

            rsp = requests.get(url)

            if rsp.ok:
                with open(file_path, 'w') as f:
                    f.write(rsp.content)
            else:
                num_missing_months += 1
                if num_missing_months >= 6:
                    raise CommandError('No data for six months!')

            if month == 1:
                year -= 1
                month = 12
            else:
                month -= 1
