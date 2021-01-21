import os

import requests
from bs4 import BeautifulSoup

from django.conf import settings
from django.core.management import BaseCommand

from openprescribing.utils import mkdir_p


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument("year", type=int)
        parser.add_argument("month", type=int)

    def handle(self, year, month, **kwargs):
        year_and_month = "{year}_{month:02d}".format(year=year, month=month)
        dir_path = os.path.join(
            settings.PIPELINE_DATA_BASEDIR, "prescribing_v2", year_and_month
        )
        mkdir_p(dir_path)

        rsp = requests.get(
            "https://opendata.nhsbsa.net/dataset/english-prescribing-data-epd"
        )
        doc = BeautifulSoup(rsp.text, "html.parser")
        filename = "epd_{year}{month:02d}.csv".format(year=year, month=month)
        urls = [a["href"] for a in doc.find_all("a") if filename in a["href"]]
        assert len(urls) == 1, urls
        rsp = requests.get(urls[0], stream=True)
        assert rsp.ok

        with open(os.path.join(dir_path, filename), "wb") as f:
            for block in rsp.iter_content(32 * 1024):
                f.write(block)
