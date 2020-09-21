import os

import requests

from django.conf import settings
from django.core.management import BaseCommand

from openprescribing.utils import mkdir_p


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument("year", type=int)
        parser.add_argument("month", type=int)

    def handle(self, year, month, **kwargs):
        year_and_month = "{year}_{month:02d}".format(year=year, month=month)
        filename = "EPD_{year}{month:02d}.csv".format(year=year, month=month)

        dir_path = os.path.join(
            settings.PIPELINE_DATA_BASEDIR, "prescribing_v2", year_and_month
        )
        csv_path = os.path.join(dir_path, filename)
        mkdir_p(dir_path)

        url = "https://storage.googleapis.com/datopian-nhs/csv/" + filename
        rsp = requests.get(url, stream=True)
        assert rsp.ok

        with open(csv_path, "wb") as f:
            for block in rsp.iter_content(32 * 1024):
                f.write(block)
