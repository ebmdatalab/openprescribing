from mock import MagicMock
from mock import patch

from django.core.management import call_command
from django.test import TestCase
from frontend.models import Presentation

from gcutils.bigquery import Client
from gcutils.bigquery import NotFound

from frontend.bq_schemas import RAW_PRESCRIBING_SCHEMA
from frontend.models import ImportLog


class CommandsTestCase(TestCase):
    fixtures = ['presentations', 'importlog']

    @patch('gcutils.bigquery.Client')
    def test_import_adqs(self, mock_client):
        mock_query = MagicMock(name='query')
        mock_query.query.return_value.rows = [
            ('0202010F0.*AA', 0.333),
        ]
        mock_client.return_value = mock_query
        call_command('import_adqs')

        # check we called bigquery with the right source table
        mock_query.query.assert_called_once()
        self.assertIn(
            "tmp_eu.raw_prescribing_data_2014_11",
            mock_query.query.call_args[0][0])

        # Check we set adq_per_quantity according to the bigquery results
        p = Presentation.objects.get(bnf_code='0202010F0AAAAAA')
        self.assertEqual(p.adq_per_quantity, 0.333)
        p = Presentation.objects.get(bnf_code='0204000I0JKKKAL')
        self.assertEqual(p.adq_per_quantity, None)


class CommandsFunctionalTestCase(TestCase):
    fixtures = ['presentations', 'importlog']

    def setUp(self):
        """Create a raw_prescribing_data table such as is expected to exist by
        ADQ calculation code.
        """
        raw_data_path = 'frontend/tests/fixtures/commands/' +\
                        'convert_hscic_prescribing/2016_01/' +\
                        'Detailed_Prescribing_Information.csv'
        year_and_month = ImportLog.objects.latest_in_category(
            'prescribing').current_at.strftime("%Y_%m")
        self.table_name = 'raw_prescribing_data_{}'.format(year_and_month)
        self.client = Client('tmp_eu')
        t1 = self.client.get_or_create_table(
            self.table_name, RAW_PRESCRIBING_SCHEMA)
        t1.insert_rows_from_csv(raw_data_path, skip_leading_rows=1)

        call_command('import_adqs')

    def test_import_adqs_functional(self):
        # These all have ADQs in the raw data
        for p in Presentation.objects.filter(bnf_code__regex='0202010B0.*AB'):
            self.assertEqual(p.adq_per_quantity, 1.0)
        # This doesn't exist in the raw data
        p = Presentation.objects.get(bnf_code='0204000I0AAAZAZ')
        self.assertEqual(p.adq_per_quantity, None)

    def tearDown(self):
        try:
            self.client.delete_table(self.table_name)
        except NotFound:
            pass
