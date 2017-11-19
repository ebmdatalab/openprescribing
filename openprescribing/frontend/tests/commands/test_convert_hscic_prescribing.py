import csv
import os

from django.conf import settings
from django.core.management import call_command
from django.test import TestCase

from django.core.management.base import CommandError

from gcutils.bigquery import Client as BQClient, NotFound
from gcutils.storage import Client as StorageClient


class CommandsTestCase(TestCase):
    def test_convert_detailed_hscic_prescribing_has_date(self):
        opts = {
            'filename': ('/home/hello/openprescribing-data/data/prescribing'
                         '/Detailed_Prescribing_Information.csv')
        }
        with self.assertRaises(CommandError):
            call_command('convert_hscic_prescribing', **opts)


class AggregateTestCase(TestCase):
    """Test that data in the "detailed" format is correctly aggregated to
    the level we currently use in the website.

    The source format has one iine for each presentation *and pack
    size*, so prescriptions of 28 paracetamol will be on a separate
    line from prescriptions of 100 paracetamol.

    The destination format has one line for paracetamol of any pack
    size.

    """
    def test_data_is_aggregated(self):
        # upload a file to GCS
        # test that the file we get back is correct
        raw_data_path = 'frontend/tests/fixtures/commands/' +\
            'convert_hscic_prescribing/2016_01/' +\
            'Detailed_Prescribing_Information.csv'
        converted_data_path = 'frontend/tests/fixtures/commands/' +\
            'convert_hscic_prescribing/2016_01/' +\
            'Detailed_Prescribing_Information_formatted.CSV'
        gcs_path = 'hscic/prescribing/2016_01/' +\
            'Detailed_Prescribing_Information.csv'

        client = StorageClient()
        bucket = client.get_bucket('ebmdatalab')
        blob = bucket.blob(gcs_path)

        with open(raw_data_path) as f:
            blob.upload_from_file(f)

        call_command('convert_hscic_prescribing', filename=raw_data_path)

        with open(converted_data_path) as f:
            rows = list(csv.reader(f))

        # there are 11 rows in the input file; 2 are for the same
        # practice/presentation and should be collapsed, and 1 is for
        # an UNKNONWN SURGERY (see issue #349)
        self.assertEqual(len(rows), 9)
        dr_chan = next(
            x for x in rows if x[1] == 'P92042' and x[2] == '0202010B0AAABAB')
        self.assertEqual(int(dr_chan[6]), 1288)  # combination of two rows

    def tearDown(self):
        table_name = 'raw_nhs_digital_data_2016_01'
        table = BQClient(settings.BQ_TMP_DATASET).get_table(table_name)
        try:
            table.gcbq_table.delete()
        except NotFound:
            pass

        table = BQClient(settings.BQ_HSCIC_DATASET).get_table('prescribing')
        table.delete_all_rows()

        try:
            os.remove('frontend/tests/fixtures/commands/' +
                      'convert_hscic_prescribing/2016_01/' +
                      'Detailed_Prescribing_Information_formatted.CSV')
        except OSError:
            pass
