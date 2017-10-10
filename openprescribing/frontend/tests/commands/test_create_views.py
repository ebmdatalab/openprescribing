import os
import unittest

from mock import patch
from mock import MagicMock

from django.core.management import call_command
from django.db import connection
from django.test import SimpleTestCase

from common import utils
from ebmdatalab.bigquery import Client
from frontend.management.commands import create_views
from frontend.models import ImportLog, PCT, PracticeStatistics
from frontend.bq_schemas import (CCG_SCHEMA, PRACTICE_STATISTICS_SCHEMA,
    PRESCRIBING_SCHEMA)
from frontend.bq_schemas import ccgs_transform, statistics_transform
from google.cloud import storage


def _mockFile(name):
    mock = MagicMock(spec=file, name=name)
    mock.configure_mock(name='frontend/tests/fixtures/commands/' + name)
    return mock


class CommandsTestCase(SimpleTestCase):
    allow_database_queries = True

    @classmethod
    def setUpClass(cls):
        if 'SKIP_BQ_LOAD' not in os.environ:
            # Create local test data from fixtures, then upload this to a
            # test project in bigquery
            call_command('loaddata',
                         'frontend/tests/fixtures/ccgs.json',
                         verbosity=0)
            call_command('loaddata',
                         'frontend/tests/fixtures/practices.json',
                         verbosity=0)
            call_command('loaddata',
                         'frontend/tests/fixtures/practice_listsizes.json',
                         verbosity=0)
            prescribing_fixture_path = os.path.join(
                'frontend', 'tests', 'fixtures', 'commands',
                'prescribing_bigquery_views_fixture.csv'
            )

            client = Client('test_hscic')

            for table_name in [
                    'normalised_prescribing_standard',
                    'normalised_prescribing_legacy']:
                table = client.get_or_create_table(
                    table_name,
                    PRESCRIBING_SCHEMA
                )
                table.insert_rows_from_csv(prescribing_fixture_path)

            table = client.get_or_create_table('ccgs', CCG_SCHEMA)
            columns = [field.name for field in CCG_SCHEMA]
            table.insert_rows_from_pg(PCT, columns, ccgs_transform)

            table = client.get_or_create_table(
                'practice_statistics',
                PRACTICE_STATISTICS_SCHEMA
            )
            columns = [field.name for field in PRACTICE_STATISTICS_SCHEMA]
            columns[0] = 'date'
            columns[-1] = 'practice_id'
            table.insert_rows_from_pg(PracticeStatistics, columns, statistics_transform)

            client = storage.Client(project='ebmdatalab')
            bucket = client.get_bucket('ebmdatalab')
            for blob in bucket.list_blobs(prefix='test_hscic/views/vw__'):
                blob.delete()

        ImportLog.objects.create(
            category='prescribing', current_at='2015-10-01')
        # Create view tables and indexes
        with open(
                'frontend/management/commands/replace_matviews.sql', 'r') as f:
            with connection.cursor() as c:
                c.execute(f.read())

    @classmethod
    def tearDownClass(cls):
        # Is this redundant?
        call_command('flush', verbosity=0, interactive=False)

    def test_existing_files_deleted(self):
        # Create a dataset fragment which should end up being deleted
        client = storage.Client(project='ebmdatalab')
        bucket = client.get_bucket('ebmdatalab')
        blob_name = ('test_hscic/views/vw__presentation_summary_by_ccg'
                     '-000000009999.csv.gz')
        blob = bucket.blob(blob_name)
        blob.upload_from_string("test", content_type="application/gzip")

        # Run import command
        call_command('create_views', dataset='test_hscic')

        # Check the bucket is no longer there
        client = storage.Client(project='ebmdatalab')
        bucket = client.get_bucket('ebmdatalab')
        prefix, suffix = blob_name.split('-')
        for blob in bucket.list_blobs(prefix=prefix):
            self.assertNotIn(suffix, blob.path)

    def test_import_create_views(self):
        call_command('create_views', dataset='test_hscic')
        with connection.cursor() as c:
            cmd = 'SELECT * FROM vw__practice_summary '
            cmd += 'ORDER BY processing_date, practice_id'
            c.execute(cmd)
            results = c.fetchall()
            self.assertEqual(len(results), 2)
            self.assertEqual(results[1][1], 'P87629')
            self.assertEqual(results[1][2], 385)
            self.assertEqual(results[1][3], 6000)
            self.assertEqual(results[1][4], 38500)

            cmd = 'SELECT * FROM vw__presentation_summary '
            cmd += 'ORDER BY processing_date, presentation_code'
            c.execute(cmd)
            results = c.fetchall()
            self.assertEqual(len(results), 4)
            self.assertEqual(results[0][1], '0703021Q0AAAAAA')
            self.assertEqual(results[0][2], 300)
            self.assertEqual(results[0][3], 3000)
            self.assertEqual(results[0][4], 30000)

            cmd = 'SELECT * FROM vw__presentation_summary_by_ccg '
            cmd += 'ORDER BY processing_date, presentation_code'
            c.execute(cmd)
            results = c.fetchall()
            self.assertEqual(len(results), 4)
            self.assertEqual(results[0][1], '03Q')
            self.assertEqual(results[0][2], '0703021Q0AAAAAA')
            self.assertEqual(results[0][3], 300)
            self.assertEqual(results[0][4], 3000)
            self.assertEqual(results[0][5], 30000)

            cmd = 'SELECT * FROM vw__chemical_summary_by_ccg '
            cmd += 'ORDER BY processing_date, chemical_id'
            c.execute(cmd)
            results = c.fetchall()
            self.assertEqual(len(results), 2)
            self.assertEqual(results[0][1], '03Q')
            self.assertEqual(results[0][2], '0703021Q0')
            self.assertEqual(results[0][3], 1110)
            self.assertEqual(results[0][4], 84000)
            self.assertEqual(results[0][5], 111000)

            cmd = 'SELECT * FROM vw__chemical_summary_by_practice '
            cmd += 'ORDER BY processing_date, practice_id'
            c.execute(cmd)
            results = c.fetchall()
            self.assertEqual(len(results), 2)
            self.assertEqual(results[0][1], 'N84014')
            self.assertEqual(results[0][2], '0703021Q0')
            self.assertEqual(results[0][3], 1110)
            self.assertEqual(results[0][4], 84000)
            self.assertEqual(results[0][5], 111000)

            cmd = 'SELECT * FROM vw__ccgstatistics '
            cmd += 'ORDER BY date, pct_id'
            c.execute(cmd)
            results = c.fetchall()
            self.assertEqual(len(results), 3)
            self.assertEqual(results[0][1], '03Q')
            self.assertEqual(results[0][5], 489.7)
            self.assertEqual(results[0][6]['oral_antibacterials_item'], 10)
