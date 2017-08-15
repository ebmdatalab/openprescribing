import os

from ebmdatalab import bigquery
from google.cloud.bigquery import SchemaField

TEST_SCHEMA = [
    SchemaField('id', 'INTEGER'),
    SchemaField('word', 'STRING'),
]


def test_load_and_fetch():
    path = os.path.join(os.path.dirname(__file__), 'test_table.csv')
    bigquery.load_data_from_file(
        'measures', 'test_table', path, TEST_SCHEMA)
    result = list(bigquery.get_rows(
        'ebmdatalab', 'measures', 'test_table'))
    assert result[0] == {'id': 1, 'word': 'hello'}
    assert result[1] == {'id': 2, 'word': 'goodbye'}
