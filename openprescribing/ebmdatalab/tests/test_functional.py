from unittest import TestCase
import os

from ebmdatalab import bigquery
from google.cloud.bigquery import SchemaField

TEST_SCHEMA = [
    SchemaField('id', 'INTEGER'),
    SchemaField('word', 'STRING'),
]


class FunctionalTests(TestCase):
    def test_load_and_fetch(self):
        path = os.path.join(os.path.dirname(__file__), 'test_table.csv')
        bigquery.load_data_from_file(
            'measures', 'test_table', path, TEST_SCHEMA)
        result = list(bigquery.get_rows(
            'ebmdatalab', 'measures', 'test_table'))
        assert result[0] == {'id': 1, 'word': 'apple'}
        assert result[1] == {'id': 2, 'word': 'banana'}
