import csv
import random

from google.cloud.bigquery import SchemaField
from google.cloud.exceptions import Conflict
from google.cloud import storage

from django.core.management import call_command
from django.test import TestCase

from ebmdatalab.bq_client import Client, TableExporter
from frontend.bq_model_tables import BQ_CCGs


class BQClientTest(TestCase):
    def setUp(self):
        self.dataset_name = 'bq_test_{:02d}'.format(random.randrange(100))

        client = Client(self.dataset_name)
        client.create_dataset()

    def tearDown(self):
        client = Client(self.dataset_name)
        client.delete_dataset()

    def test_the_lot(self):
        client = Client(self.dataset_name)

        schema = [
            SchemaField('a', 'INTEGER'),
            SchemaField('b', 'STRING'),
        ]

        headers = ['a', 'b']
        rows = [
            (1, 'apple'),
            (2, 'banana'),
            (3, 'coconut'),
        ]

        t1 = client.get_or_create_table('t1', schema)
        t2 = client.get_or_create_table('t2', schema)

        # Test Table.insert_rows_from_csv
        t1.insert_rows_from_csv('ebmdatalab/tests/test_table.csv')

        self.assertEqual(list(t1.get_rows()), rows)

        # Test Table.insert_rows_from_query
        t2.insert_rows_from_query('SELECT * FROM {} WHERE a > 1 ORDER BY a'.format(t1.qualified_name))

        self.assertEqual(list(t2.get_rows()), rows[1:])

        # Test Client.query
        results = client.query('SELECT * FROM {} WHERE a > 2 ORDER BY a'.format(t1.qualified_name))

        self.assertEqual(list(results.rows), rows[2:])

        # Test TableExporter.export_to_storage and TableExporter.download_from_storage_and_unzip
        t1_exporter = TableExporter(t1, 'test_bq_client/test_table-')
        t1_exporter.export_to_storage()

        with t1_exporter.download_from_storage_and_unzip() as f:
            data = list(csv.reader(f))

        self.assertEqual(data, [[str(x) for x in row] for row in [headers] + rows])

        # Test Table.insert_rows_from_storage
        self.upload_to_storage('ebmdatalab/tests/test_table.csv', 'test_bq_client/test_table.csv')

        t2.insert_rows_from_storage('gs://ebmdatalab/test_bq_client/test_table.csv')

        self.assertEqual(list(t2.get_rows()), rows)

        # Test Client.get_or_create_table_referencing_storage
        self.upload_to_storage('ebmdatalab/tests/test_table_headers.csv', 'test_bq_client/test_table_headers.csv')

        schema = [
            {'name': 'a', 'type': 'integer'},
            {'name': 'b', 'type': 'string'},
        ]

        t3 = client.get_or_create_table_referencing_storage('t3', schema, 'test_bq_client/test_table_headers.csv')

        results = client.query('SELECT * FROM {}'.format(t3.qualified_name))

        self.assertEqual(list(results.rows), rows)

        self.upload_to_storage(
            'ebmdatalab/tests/test_table_headers_2.csv',
            'test_bq_client/test_table_headers.csv'
        )

        results = client.query('SELECT * FROM {}'.format(t3.qualified_name))

        self.assertEqual(list(results.rows), rows + [(4, u'damson')])

    def upload_to_storage(self, local_path, storage_path):
        client = storage.client.Client(project='ebmdatalab')
        bucket = client.bucket('ebmdatalab')
        blob = bucket.blob(storage_path)
        with open(local_path) as f:
            blob.upload_from_file(f)


class TestBQModel(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command('import_org_names', ccg='frontend/tests/fixtures/commands/eccg.csv')

    def test_insert_rows_from_pg(self):
        bq_ccgs = BQ_CCGs()
        bq_ccgs.insert_rows_from_pg()
        client = Client('test_hscic')
        results = client.query('SELECT * FROM test_hscic.ccgs')
        self.assertEqual(len(list(results.rows)), 3)
