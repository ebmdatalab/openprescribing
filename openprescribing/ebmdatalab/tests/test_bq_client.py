import csv
import gzip
import os
from tempfile import mkdtemp

from google.cloud.bigquery import SchemaField
from google.cloud.exceptions import Conflict
from google.cloud import storage

from django.core.management import call_command
from django.test import TestCase

from ebmdatalab.bq_client import Client
from frontend.bq_model_tables import BQ_CCGs


class BQClientTest(TestCase):
    def setUp(self):
        # TODO Rationalise this
        client = Client('sandpit3')

        try:
            client.create_dataset()
        except Conflict:
            pass

        schema = [
            SchemaField('a', 'INTEGER'),
            SchemaField('b', 'STRING'),
        ]

        t1 = client.get_or_create_table('t1', schema)
        t2 = client.get_or_create_table('t2', schema)

    def test_the_lot(self):
        client = Client('sandpit3')
        t1 = client.get_table('t1')
        t2 = client.get_table('t2')

        headers = ['a', 'b']
        rows = [
            (1, 'apple'),
            (2, 'banana'),
            (3, 'coconut'),
        ]

        csv_path = 'ebmdatalab/tests/test_table.csv'

        t1.insert_rows_from_csv(csv_path)

        self.assertEqual(list(t1.get_rows()), rows)

        t2.insert_rows_from_query('SELECT * FROM sandpit3.t1 WHERE a > 1 ORDER BY a')

        self.assertEqual(list(t2.get_rows()), rows[1:])

        results = client.query('SELECT * FROM sandpit3.t1 WHERE a > 2 ORDER BY a')

        self.assertEqual(list(results.rows), rows[2:])

        t1.export_to_storage()

        with t1.download_from_storage_and_unzip() as f:
            data = list(csv.reader(f))

        self.assertEqual(data, [[str(x) for x in row] for row in [headers] + rows])

        client = storage.client.Client(project='ebmdatalab')
        bucket = client.get_bucket('ebmdatalab')
        blob = bucket.blob('test_bq_client/test_table.csv')

        with open(csv_path) as f:
            blob.upload_from_file(f)

        t2.insert_rows_from_storage('gs://ebmdatalab/test_bq_client/blob.csv')

        self.assertEqual(list(t2.get_rows()), rows)


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
