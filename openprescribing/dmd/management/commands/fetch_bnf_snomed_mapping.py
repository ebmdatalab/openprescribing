"""
Downloads and unzips the latest BNF SNOMED mapping to
PIPELINE_DATA_BASEDIR/bnf_snomed_mapping/[yyyy_mm_dd]/

Does nothing if file already downloaded.
"""

import glob
import os
from pathlib import Path
import re
from urllib.parse import urljoin, urlparse, unquote
import zipfile

from django.conf import settings
from django.core.management import BaseCommand

import requests
from bs4 import BeautifulSoup

from openprescribing.utils import mkdir_p


class Command(BaseCommand):
    help = __doc__

    def handle(self, *args, **kwargs):
        page_url = "https://www.nhsbsa.nhs.uk/prescription-data/understanding-our-data/bnf-snomed-mapping"
        filename_re = re.compile(
            r"^BNF Snomed Mapping data (?P<date>20\d{6})\.zip$", re.IGNORECASE
        )

        rsp = requests.get(page_url)
        rsp.raise_for_status()
        doc = BeautifulSoup(rsp.text, "html.parser")

        matches = []
        for a_tag in doc.find_all("a", href=True):
            url = urljoin(page_url, a_tag["href"])
            filename = Path(unquote(urlparse(url).path)).name
            match = filename_re.match(filename)
            if match:
                matches.append((match.group("date"), url, filename))

        if not matches:
            raise RuntimeError(f"Found no URLs matching {filename_re} at {page_url}")

        # Sort by release date and get the latest
        matches.sort()
        datestamp, url, filename = matches[-1]

        release_date = datestamp[:4] + "_" + datestamp[4:6] + "_" + datestamp[6:]
        dir_path = os.path.join(
            settings.PIPELINE_DATA_BASEDIR, "bnf_snomed_mapping", release_date
        )
        zip_path = os.path.join(dir_path, filename)

        if glob.glob(os.path.join(dir_path, "*.xlsx")):
            return

        mkdir_p(dir_path)

        rsp = requests.get(url, stream=True)
        rsp.raise_for_status()

        with open(zip_path, "wb") as f:
            for block in rsp.iter_content(32 * 1024):
                f.write(block)

        with zipfile.ZipFile(zip_path) as zf:
            zf.extractall(dir_path)
