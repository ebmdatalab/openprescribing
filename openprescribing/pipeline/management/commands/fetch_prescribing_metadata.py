import json
import os
import re

from bs4 import BeautifulSoup
import requests

from django.conf import settings
from django.core.management import BaseCommand

from openprescribing.utils import mkdir_p


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('dataset', choices=['addresses', 'chemicals'])

    def handle(self, *args, **kwargs):
        # The page lists available downloads.  The data is stored in a JSON
        # object.
        url = 'https://data.gov.uk/dataset/176ae264-2484-4afe-a297-d51798eb8228/gp-practice-prescribing-data-presentation-level'
        rsp = requests.get(url)
        doc = BeautifulSoup(rsp.content, 'html.parser')
        tag = doc.find('script', type='application/ld+json')
        metadata = json.loads(tag.text)

        filename_fragment = {
            'addresses': 'ADDR%20BNFT',
            'chemicals': 'CHEM%20SUBS',
        }[kwargs['dataset']]
        pattern = 'T(\d{4})(\d{2})' + filename_fragment + '.CSV'

        urls = [
            record['contentUrl'] for record in metadata['distribution']
            if filename_fragment in record['contentUrl']
        ]

        # Iterate over the URLs, newest first, downloading as we go, and
        # stopping once we find a URL that we have already downloaded.
        for url in sorted(urls, key=lambda url: url.split('/')[-1], reverse=True):
            filename = url.split('/')[-1]
            tmp_filename = filename + '.tmp'
            match = re.match(pattern, filename)
            year_and_month = '_'.join(match.groups())

            dir_path = os.path.join(
                settings.PIPELINE_DATA_BASEDIR,
                'prescribing_metadata',
                year_and_month
            )

            if os.path.exists(os.path.join(dir_path, filename)):
                break

            # Older versions of the data have slightly different filenames.
            if os.path.exists(os.path.join(dir_path, filename.replace('%20', '+'))):
                break

            mkdir_p(dir_path)

            rsp = requests.get(url)
            assert rsp.ok

            # Since we check for the presence of the file to determine whether
            # this data has already been fetched, we write to a temporary file
            # and then rename it.
            with open(os.path.join(dir_path, tmp_filename), 'w') as f:
                f.write(rsp.content)

            os.rename(
                os.path.join(dir_path, tmp_filename),
                os.path.join(dir_path, filename)
            )
