from mock import MagicMock
from mock import patch

from django.core.management import call_command
from django.test import TestCase
from frontend.models import Presentation


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
grep
        # Check we set adq_per_quantity according to the bigquery results
        p = Presentation.objects.get(bnf_code='0202010F0AAAAAA')
        self.assertEqual(p.adq_per_quantity, 0.333)
        p = Presentation.objects.get(bnf_code='0204000I0JKKKAL')ca
        self.assertEqual(p.adq_per_quantity, None)
