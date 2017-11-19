import csv
import tempfile

from mock import patch

from django.conf import settings
from django.core.management import call_command
from django.test import TestCase

from frontend.management.commands.convert_hscic_prescribing import Command
from django.core.management.base import CommandError

from gcutils.bigquery import Client as BQClient, NotFound
from gcutils.storage import Client as StorageClient


class CommandsTestCase(TestCase):

    @patch('frontend.management.commands.convert_hscic_prescribing.Command'
           '.aggregate_nhs_digital_data')
    def test_convert_detailed_hscic_prescribing_call(self, method):
        method.return_value = 'filename.csv'
        opts = {
            'filename': ('/home/hello/openprescribing-data/data/prescribing'
                         '/2017_03/Detailed_Prescribing_Information.csv')
        }
        call_command('convert_hscic_prescribing', **opts)
        method.assert_called_with(
            ('hscic/prescribing/2017_03/'
             'Detailed_Prescribing_Information.csv'),
            ('/home/hello/openprescribing-data/data/prescribing'
             '/2017_03/Detailed_Prescribing_Information_formatted.CSV'),
            '2017_03_01')

    @patch('frontend.management.commands.convert_hscic_prescribing.Command'
           '.aggregate_nhs_digital_data')
    def test_convert_detailed_hscic_prescribing_has_date(self, method):
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
        test_file = 'frontend/tests/fixtures/commands/'
        test_file += 'Detailed_Prescribing_Information.csv'
        object_path = 'test_hscic/prescribing/sample.csv'
        client = StorageClient()
        bucket = client.get_bucket('ebmdatalab')
        blob = bucket.blob(object_path)

        with open(test_file, 'rb') as my_file:
            blob.upload_from_file(my_file)

        target = tempfile.NamedTemporaryFile(mode='r+')
        cmd = Command()
        cmd.aggregate_nhs_digital_data(object_path, target.name, date='2016_01_01')
        target.seek(0)
        rows = list(csv.reader(open(target.name, 'rU')))
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
