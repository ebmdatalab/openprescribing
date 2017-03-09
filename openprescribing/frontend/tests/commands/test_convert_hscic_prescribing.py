import csv
import datetime
import os
import tempfile
import unittest

from google.cloud import storage

from django.core.management import call_command
from django.test import TestCase

from frontend.management.commands.convert_hscic_prescribing import Command


class CommandsTestCase(TestCase):

    @unittest.skipIf("TRAVIS" in os.environ and os.environ["TRAVIS"],
                     "Skipping this test on Travis CI.")
    def test_convert_hscic_prescribing(self):
        args = []
        test_file = 'frontend/tests/fixtures/commands/'
        test_file += 'hscic_prescribing_sample.csv'
        opts = {
            'filename': test_file,
            'is_test': True
        }
        call_command('convert_hscic_prescribing', *args, **opts)

        test_output = 'frontend/tests/fixtures/commands/'
        test_output += 'hscic_prescribing_sample_test.CSV'
        reader = csv.reader(open(test_output, 'rU'))
        rows = []
        for row in reader:
            rows.append(row)

        os.remove(test_output)
        self.assertEqual(len(rows), 51)

        # Test the basics are in the order expected by our COPY statement:
        # pct_id,practice_id,presentation_code,
        # total_items,actual_cost,
        # quantity,processing_date,price_per_unit
        self.assertEqual(rows[0][0], 'RXA')
        self.assertEqual(rows[0][1], 'N81646')
        self.assertEqual(rows[0][2], '0102000N0AAABAB')
        self.assertEqual(rows[0][3], '1')
        self.assertEqual(rows[0][4], '0.7')
        self.assertEqual(rows[0][5], '12')
        self.assertEqual(rows[0][6], '2014-10-01')


class AggregateTestCase(TestCase):
    """Do stuff
    """
    def setUp(self):
        # upload a file to GCS
        # test that the file we get back is correct
        test_file = 'frontend/tests/fixtures/commands/'
        test_file += 'detailed_prescribing.csv'
        bucket_name = 'ebmdatalab'
        object_name = 'test_hscic/prescribing/sample.csv'
        client = storage.client.Client(project='ebmdatalab')
        bucket = client.get_bucket(bucket_name)
        blob = storage.Blob(object_name, bucket)

        with open(test_file, 'rb') as my_file:
            blob.upload_from_file(my_file)
        self.gcs_uri = "gs://ebmdatalab/%s" % object_name

    def test_data_is_aggregated(self):
        target = tempfile.NamedTemporaryFile(mode='r+')
        date = datetime.date(2011, 12, 1)
        cmd = Command()
        cmd.date = date
        cmd.aggregate_nhs_digital_data(
            self.gcs_uri, target.name, date='2016-01-01')
        target.seek(0)
        rows = list(csv.reader(open(target.name, 'rU')))
        # there are 11 rows in the input file; 2 are for the same
        # practice/presentation and should be collapsed, and 1 is for
        # an UNKNONWN SURGERY (see issue #349)
        self.assertEqual(len(rows), 9)
        dr_chan = next(
            x for x in rows if x[-2] == 'P92042' and x[0] == '0202010B0AAABAB')
        self.assertEqual(int(dr_chan[5]), 644)  # combination of two rows
