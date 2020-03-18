"""
Downloads and unzips the latest BNF SNOMED mapping to
PIPELINE_DATA_BASEDIR/bnf_snomed_mapping/[yyyy_mm_dd]/

Does nothing if file already downloaded.
"""

import glob
import os
import zipfile

from django.conf import settings
from django.core.management import BaseCommand

import requests
from bs4 import BeautifulSoup

from openprescribing.utils import mkdir_p


class Command(BaseCommand):
    help = __doc__

    def handle(self, *args, **kwargs):
        base_url = "https://www.nhsbsa.nhs.uk"

        rsp = requests.get(
            base_url + "/prescription-data/understanding-our-data/bnf-snomed-mapping"
        )
        doc = BeautifulSoup(rsp.text, "html.parser")

        href = None
        for a in doc.find_all("a"):
            if a["href"].endswith(".zip"):
                assert href is None, "Found more than one zipfile"
                href = a["href"]

        filename = href.split("/")[-1]
        datestamp = filename.split(".")[0].split("%20")[-1]
        release_date = datestamp[:4] + "_" + datestamp[4:6] + "_" + datestamp[6:]

        dir_path = os.path.join(
            settings.PIPELINE_DATA_BASEDIR, "bnf_snomed_mapping", release_date
        )
        zip_path = os.path.join(dir_path, filename)

        if glob.glob(os.path.join(dir_path, "*.xlsx")):
            print("Already fetched")
            return

        mkdir_p(dir_path)

        rsp = requests.get(base_url + href, stream=True)
        rsp.raise_for_status()

        with open(zip_path, "wb") as f:
            for block in rsp.iter_content(32 * 1024):
                f.write(block)

        with zipfile.ZipFile(zip_path) as zf:
            zf.extractall(dir_path)
