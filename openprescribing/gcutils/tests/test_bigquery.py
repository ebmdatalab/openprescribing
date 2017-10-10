import csv
import random
import tempfile

from google.cloud import storage

from django.test import TestCase

from gcutils.bigquery import Client, TableExporter, build_schema
from gcutils.table_dumper import TableDumper

from frontend.models import PCT


class BQClientTest(TestCase):
    def setUp(self):
        self.n = random.randrange(100)
        self.dataset_name = 'bq_test_{:02d}'.format(self.n)

        client = Client(self.dataset_name)
        client.create_dataset()

        self.storage_paths = set()

    def tearDown(self):
        client = Client(self.dataset_name)
        client.delete_dataset()

        client = storage.client.Client(project='ebmdatalab')
        bucket = client.bucket('ebmdatalab')
        for storage_path in self.storage_paths:
            blob = bucket.blob(storage_path)
            blob.delete()

    def test_the_lot(self):
        client = Client(self.dataset_name)

        schema = build_schema(
            ('a', 'INTEGER'),
            ('b', 'STRING'),
        )

        headers = ['a', 'b']
        rows = [
            (1, 'apple'),
            (2, 'banana'),
            (3, 'coconut'),
        ]

        t1 = client.get_or_create_table('t1', schema)

        # Test Table.insert_rows_from_csv
        t1.insert_rows_from_csv('gcutils/tests/test_table.csv')

        self.assertEqual(sorted(t1.get_rows()), rows)

        # Test Table.insert_rows_from_query
        t2 = client.get_table('t2')

        sql = 'SELECT * FROM {} WHERE a > 1'.format(t1.qualified_name)
        t2.insert_rows_from_query(sql)

        self.assertEqual(sorted(t2.get_rows()), rows[1:])

        # Test Client.query
        sql = 'SELECT * FROM {} WHERE a > 2'.format(t1.qualified_name)
        results = client.query(sql)

        self.assertEqual(sorted(results.rows), rows[2:])

        # Test TableExporter.export_to_storage and
        # TableExporter.download_from_storage_and_unzip
        t1_exporter = TableExporter(
            t1,
            'test_bq_client/test_table-{}'.format(self.n)
        )
        t1_exporter.export_to_storage()

        with tempfile.NamedTemporaryFile(mode='r+') as f:
            t1_exporter.download_from_storage_and_unzip(f)
            f.seek(0)
            reader = csv.reader(f)
            data = [reader.next()] + sorted(reader)

        self.assertEqual(data, [map(str, row) for row in [headers] + rows])

        # Test Table.insert_rows_from_storage
        self.upload_to_storage(
            'gcutils/tests/test_table.csv',
            'test_bq_client/test_table-{}.csv'.format(self.n)
        )

        t2.insert_rows_from_storage(
            'gs://ebmdatalab/test_bq_client/test_table-{}.csv'.format(self.n)
        )

        self.assertEqual(sorted(t2.get_rows()), rows)

        # Test Client.get_or_create_storage_backed_table
        self.upload_to_storage(
            'gcutils/tests/test_table_headers.csv',
            'test_bq_client/test_table_headers-{}.csv'.format(self.n)
        )

        schema = [
            {'name': 'a', 'type': 'integer'},
            {'name': 'b', 'type': 'string'},
        ]

        t3 = client.get_or_create_storage_backed_table(
            't3',
            schema,
            'test_bq_client/test_table_headers-{}.csv'.format(self.n)
        )

        results = client.query('SELECT * FROM {}'.format(t3.qualified_name))

        self.assertEqual(sorted(results.rows), rows)

        self.upload_to_storage(
            'gcutils/tests/test_table_headers_2.csv',
            'test_bq_client/test_table_headers-{}.csv'.format(self.n)
        )

        results = client.query('SELECT * FROM {}'.format(t3.qualified_name))

        self.assertEqual(sorted(results.rows), rows + [(4, u'damson')])

        # Test Client.create_table_with_view
        sql = 'SELECT * FROM {} WHERE a > 1'.format(t1.full_qualified_name)

        t4 = client.create_table_with_view('t4', sql, False)

        results = client.query('SELECT * FROM {}'.format(t4.qualified_name))

        self.assertEqual(sorted(results.rows), rows[1:])

        # Test Client.insert_rows_from_pg
        PCT.objects.create(code='ABC', name='CCG 1')
        PCT.objects.create(code='XYZ', name='CCG 2')

        def transformer(row):
            return [ord(row[0][0]), row[1]]
        t1.insert_rows_from_pg(PCT, ['code', 'name'], transformer)

        self.assertEqual(sorted(t1.get_rows()), [(65, 'CCG 1'), (88, 'CCG 2')])

    def upload_to_storage(self, local_path, storage_path):
        client = storage.client.Client(project='ebmdatalab')
        bucket = client.bucket('ebmdatalab')
        blob = bucket.blob(storage_path)
        with open(local_path) as f:
            blob.upload_from_file(f)
        self.storage_paths.add(storage_path)
