import csv
import os

from django.conf import settings
from django.core.management import call_command
from django.test import TestCase

from django.core.management.base import CommandError

from gcutils.bigquery import Client as BQClient, NotFound, results_to_dicts
from gcutils.storage import Client as StorageClient

from frontend.bq_schemas import PRESCRIBING_SCHEMA


class ConvertHscicPrescribingTests(TestCase):
    """Test that data in the "detailed" format is correctly aggregated to
    the level we currently use in the website.

    The source format has one iine for each presentation *and pack
    size*, so prescriptions of 28 paracetamol will be on a separate
    line from prescriptions of 100 paracetamol.

    The destination format has one line for paracetamol of any pack
    size.

    """
    def test_data_is_aggregated(self):
        # there are 11 rows in the input file; 2 are for the same
        # practice/presentation and should be collapsed, and 1 is for
        # an UNKNONWN SURGERY (see issue #349)

        raw_data_path = 'frontend/tests/fixtures/commands/' +\
            'convert_hscic_prescribing/2016_01/' +\
            'Detailed_Prescribing_Information.csv'
        converted_data_path = 'frontend/tests/fixtures/commands/' +\
            'convert_hscic_prescribing/2016_01/' +\
            'Detailed_Prescribing_Information_formatted.CSV'
        gcs_path = 'hscic/prescribing/2016_01/' +\
            'Detailed_Prescribing_Information.csv'

        client = StorageClient()
        bucket = client.get_bucket()
        blob = bucket.blob(gcs_path)

        with open(raw_data_path) as f:
            blob.upload_from_file(f)

        call_command('convert_hscic_prescribing', filename=raw_data_path)

        # Test that data added to prescribing table
        client = BQClient()
        sql = '''SELECT *
        FROM {dataset}.prescribing
        WHERE month = TIMESTAMP('2016-01-01')'''.format(
            dataset=settings.BQ_HSCIC_DATASET,
        )
        rows = list(results_to_dicts(client.query(sql)))
        self.assertEqual(len(rows), 9)
        for row in rows:
            if row['practice'] == 'P92042' and \
                    row['bnf_code'] == '0202010B0AAABAB':
                self.assertEqual(row['quantity'], 1288)

        # Test that downloaded data is correct
        with open(converted_data_path) as f:
            rows = list(csv.reader(f))

        self.assertEqual(len(rows), 9)
        for row in rows:
            if row[1] == 'P92042' and row[2] == '0202010B0AAABAB':
                self.assertEqual(row[6], '1288')

    def test_filename_has_date(self):
        with self.assertRaises(CommandError):
            call_command(
                'convert_hscic_prescribing',
                filename='Detailed_Prescribing_Information.csv'
            )

    def setUp(self):
        client = BQClient(settings.BQ_HSCIC_DATASET)
        table = client.get_or_create_table('prescribing', PRESCRIBING_SCHEMA)

    def tearDown(self):
        table_name = 'raw_prescribing_data_2016_01'
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
