import csv
import random
import tempfile

from google.cloud.bigquery import SchemaField
from google.cloud import storage

from django.test import TestCase

from ebmdatalab.bigquery import Client, TableExporter


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

        # Test Table.insert_rows_from_csv
        t1.insert_rows_from_csv('ebmdatalab/tests/test_table.csv')

        self.assertEqual(sorted(t1.get_rows()), rows)

        # Test Table.insert_rows_from_query
        t2 = client.get_table_ref('t2')

        sql = 'SELECT * FROM {} WHERE a > 1'.format(t1.qualified_name)
        t2.insert_rows_from_query(sql)

        t2 = client.get_table('t2')

        self.assertEqual(sorted(t2.get_rows()), rows[1:])

        # Test Client.query
        sql = 'SELECT * FROM {} WHERE a > 2'.format(t1.qualified_name)
        results = client.query(sql)

        self.assertEqual(sorted(results.rows), rows[2:])

        # Test TableExporter.export_to_storage and
        # TableExporter.download_from_storage_and_unzip
        t1_exporter = TableExporter(t1, 'test_bq_client/test_table-')
        t1_exporter.export_to_storage()

        with tempfile.NamedTemporaryFile(mode='r+') as f:
            t1_exporter.download_from_storage_and_unzip(f)
            f.seek(0)
            reader = csv.reader(f)
            data = [reader.next()] + sorted(reader)

        self.assertEqual(data, [map(str, row) for row in [headers] + rows])

        # Test Table.insert_rows_from_storage
        self.upload_to_storage(
            'ebmdatalab/tests/test_table.csv',
            'test_bq_client/test_table.csv'
        )

        t2.insert_rows_from_storage(
            'gs://ebmdatalab/test_bq_client/test_table.csv'
        )

        self.assertEqual(sorted(t2.get_rows()), rows)

        # Test Client.get_or_create_storage_backed_table
        self.upload_to_storage(
            'ebmdatalab/tests/test_table_headers.csv',
            'test_bq_client/test_table_headers.csv'
        )

        schema = [
            {'name': 'a', 'type': 'integer'},
            {'name': 'b', 'type': 'string'},
        ]

        t3 = client.get_or_create_storage_backed_table(
            't3',
            schema,
            'test_bq_client/test_table_headers.csv'
        )

        results = client.query('SELECT * FROM {}'.format(t3.qualified_name))

        self.assertEqual(sorted(results.rows), rows)

        self.upload_to_storage(
            'ebmdatalab/tests/test_table_headers_2.csv',
            'test_bq_client/test_table_headers.csv'
        )

        results = client.query('SELECT * FROM {}'.format(t3.qualified_name))

        self.assertEqual(sorted(results.rows), rows + [(4, u'damson')])

        # Test Client.create_table_with_view
        sql = 'SELECT * FROM {} WHERE a > 1'.format(t1.qualified_name)

        t4 = client.create_table_with_view('t4', sql, False)

        results = client.query('SELECT * FROM {}'.format(t4.qualified_name))

        self.assertEqual(sorted(results.rows), rows[1:])

    def upload_to_storage(self, local_path, storage_path):
        client = storage.client.Client(project='ebmdatalab')
        bucket = client.bucket('ebmdatalab')
        blob = bucket.blob(storage_path)
        with open(local_path) as f:
            blob.upload_from_file(f)
