from StringIO import StringIO
import requests
from zipfile import ZipFile
import datetime
import os

from django.conf import settings
from django.core.management import BaseCommand

"""Practice and CCG metadata, keyed by code.

Similar data, pertaining to specific points in time, is also found in
the files downloaded to `data/raw_data/T<datestamp>ADDR+BNFT.CSV`.

We prefer data from these files to the `ADDR+BNFT` versions, but the
data we download here is only available as current data; this means we
would lack address information for historic data points if we only
relied on these org files.

This data is therefore worth updating every month.

"""


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('--ccg', action='store_true')
        parser.add_argument('--practice', action='store_true')
        parser.add_argument('--postcode', action='store_true')

    def handle(self, *args, **kwargs):
        self.verbose = (kwargs['verbosity'] > 1)

        if kwargs['practice']:
            self.fetch_and_extract_zipped_csv('epraccur', 'practice_details')
        if kwargs['ccg']:
            self.fetch_and_extract_zipped_csv('eccg', 'ccg_details')
        if kwargs['postcode']:
            self.fetch_and_extract_zipped_csv('gridall', 'nhs_postcode_file')

    def fetch_and_extract_zipped_csv(self, base_filename, dest_dirname):
        """Grab a zipfile from a url, and extract a CSV.
        """

        zip_filename = base_filename + '.zip'
        url = 'https://files.digital.nhs.uk/assets/ods/current/' + zip_filename

        buf = StringIO()
        buf.write(requests.get(url).content)
        buf.flush()
        zipfile = ZipFile(buf)

        dest_dir = os.path.join(
            settings.PIPELINE_DATA_BASEDIR,
            dest_dirname,
            datetime.datetime.today().strftime('%Y_%m'),
        )

        csv_filename = base_filename + '.csv'
        zipfile.extract(csv_filename, dest_dir)
