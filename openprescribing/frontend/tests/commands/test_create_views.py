from datetime import date
import os

from django.core.management import call_command
from django.db import connection
from django.test import SimpleTestCase

from gcutils.bigquery import Client
from frontend.models import ImportLog, PCT, Practice, PracticeStatistics
from frontend.bq_schemas import (CCG_SCHEMA, PRACTICE_STATISTICS_SCHEMA,
                                 PRACTICE_SCHEMA, PRESCRIBING_SCHEMA)
from frontend.bq_schemas import ccgs_transform, statistics_transform
from frontend.management.commands import create_views
from gcutils.storage import Client as StorageClient


class CommandsTestCase(SimpleTestCase):
    allow_database_queries = True

    @classmethod
    def setUpClass(cls):
        # If you set SKIP_BQ_LOAD, you will also want to set BQ_NONCE to reuse
        # the BQ tables that have already been set up.
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

            client = Client('hscic')

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

            table = client.get_or_create_table('practices', PRACTICE_SCHEMA)
            columns = [field.name for field in PRACTICE_SCHEMA]
            table.insert_rows_from_pg(Practice, columns)

            table = client.get_or_create_table(
                'practice_statistics',
                PRACTICE_STATISTICS_SCHEMA
            )
            columns = [field.name for field in PRACTICE_STATISTICS_SCHEMA]
            columns[0] = 'date'
            columns[-1] = 'practice_id'
            table.insert_rows_from_pg(
                PracticeStatistics,
                columns,
                statistics_transform
            )

            client = StorageClient()
            bucket = client.get_bucket()
            for blob in bucket.list_blobs(prefix='hscic/views/vw__'):
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
        client = StorageClient()
        bucket = client.get_bucket()
        blob_name = ('hscic/views/vw__presentation_summary_by_ccg'
                     '-000000009999.csv.gz')
        blob = bucket.blob(blob_name)
        blob.upload_from_string("test", content_type="application/gzip")

        # Run import command
        call_command('create_views')

        # Check the bucket is no longer there
        client = StorageClient()
        bucket = client.get_bucket()
        prefix, suffix = blob_name.split('-')
        for blob in bucket.list_blobs(prefix=prefix):
            self.assertNotIn(suffix, blob.path)

    def test_import_create_views(self):
        call_command('create_views')
        with connection.cursor() as c:
            # ~~~~~
            # vw__presentation_summary
            # ~~~~~

            cmd = 'SELECT * FROM vw__practice_summary '
            cmd += 'ORDER BY processing_date, practice_id'
            c.execute(cmd)
            col_names = [col[0] for col in c.description]
            results = [dict(zip(col_names, row)) for row in c.fetchall()]

            self.assertEqual(len(results), 10)  # 2 months * 5 practices

            expected = {
                    'processing_date': date(2015, 1, 1),
                    'practice_id': 'B82018',
                    'items': 21,  # 5 + 7 + 9
            }
            self.assert_dicts_equal(expected, results[0])

            # ~~~~~
            # vw__presentation_summary
            # ~~~~~

            cmd = 'SELECT * FROM vw__presentation_summary '
            cmd += 'ORDER BY processing_date, presentation_code'
            c.execute(cmd)
            col_names = [col[0] for col in c.description]
            results = [dict(zip(col_names, row)) for row in c.fetchall()]

            self.assertEqual(len(results), 6)  # 2 months * 3 presentations

            expected = {
                    'processing_date': date(2015, 1, 1),
                    'presentation_code': '0703021P0AAAAAA',
                    'items': 15,  # 1 + 2 + 3 + 4 + 5
            }
            self.assert_dicts_equal(expected, results[0])

            # ~~~~~
            # vw__presentation_summary_by_ccg
            # ~~~~~

            cmd = 'SELECT * FROM vw__presentation_summary_by_ccg '
            cmd += 'ORDER BY processing_date, presentation_code, pct_id'
            c.execute(cmd)
            col_names = [col[0] for col in c.description]
            results = [dict(zip(col_names, row)) for row in c.fetchall()]

            self.assertEqual(len(results), 12)  # 2 months * 3 presentations * 2 CCGs

            expected = {
                    'processing_date': date(2015, 1, 1),
                    'pct_id': '03Q',
                    'presentation_code': '0703021P0AAAAAA',
                    'items': 9,  # 4 + 5
            }
            self.assert_dicts_equal(expected, results[0])

            expected = {
                    'processing_date': date(2015, 1, 1),
                    'pct_id': '03V',
                    'presentation_code': '0703021P0AAAAAA',
                    'items': 6,  # 1 + 2 + 3
            }
            self.assert_dicts_equal(expected, results[1])

            # ~~~~~
            # vw__chemical_summary_by_ccg
            # ~~~~~

            cmd = 'SELECT * FROM vw__chemical_summary_by_ccg '
            cmd += 'ORDER BY processing_date, chemical_id, pct_id'
            c.execute(cmd)
            col_names = [col[0] for col in c.description]
            results = [dict(zip(col_names, row)) for row in c.fetchall()]

            self.assertEqual(len(results), 8)  # 2 months * 2 chemicals * 2 CCGs

            expected = {
                    'processing_date': date(2015, 1, 1),
                    'pct_id': '03Q',
                    'chemical_id': '0703021Q0',
                    'items': 30,  # 6 + 8 + 7 + 9
            }
            self.assert_dicts_equal(expected, results[2])

            expected = {
                    'processing_date': date(2015, 1, 1),
                    'pct_id': '03V',
                    'chemical_id': '0703021Q0',
                    'items': 30,  # 3 + 5 + 4 + 6 + 5 + 7
            }
            self.assert_dicts_equal(expected, results[3])

            # ~~~~~
            # vw__chemical_summary_by_practice
            # ~~~~~

            cmd = 'SELECT * FROM vw__chemical_summary_by_practice '
            cmd += 'ORDER BY processing_date, practice_id'
            c.execute(cmd)
            col_names = [col[0] for col in c.description]
            results = [dict(zip(col_names, row)) for row in c.fetchall()]

            self.assertEqual(len(results), 20)  # 2 months * 2 chemicals * 5 practices

            expected = {
                    'processing_date': date(2015, 1, 1),
                    'practice_id': 'B82018',
                    'chemical_id': '0703021Q0',
                    'items': 16,
            }
            self.assert_dicts_equal(expected, results[1])

            # ~~~~~
            # vw__ccgstatistics
            # ~~~~~

            cmd = 'SELECT * FROM vw__ccgstatistics ORDER BY date, pct_id'
            c.execute(cmd)
            col_names = [col[0] for col in c.description]
            results = [dict(zip(col_names, row)) for row in c.fetchall()]

            self.assertEqual(len(results), 4)  # 2 months * 2 CCGs

            # For 03Q and 2015_01, we expect the calculation to include values
            # for N84014 and B82018, but not K83622, as it moved to 03V after
            # 2015_01.
            expected = {
                    'date': date(2015, 1, 1),
                    'pct_id': '03Q',
                    'name': 'NHS Vale of York',
                    'total_list_size': 612,  # 288 + 324
                    'astro_pu_items': 502.2,  # 231.1 + 271.1
                    'astro_pu_cost': 342.2,  # 161.1 + 181.1
                    'star_pu.oral_antibacterials_item': 50.2,  # 23.1 + 27.1
            }
            self.assert_dicts_equal(expected, results[0])

            # For 03V and 2015_01, we expect the calculation to include values
            # for P87629 and K83059, and also K83622 even though it was in 03Q
            # for 2015_01.
            expected = {
                    'date': date(2015, 1, 1),
                    'pct_id': '03V',
                    'name': 'NHS Corby',
                    'total_list_size': 648,  # 180 + 216 + 252
                    'astro_pu_items': 453.3,  # 111.1 + 151.1 + 191.1
                    'astro_pu_cost': 363.3,  # 101.1 + 121.1 + 141.1
                    'star_pu.oral_antibacterials_item': 45.3,  # 11.1 + 15.1 + 19.1
            }
            self.assert_dicts_equal(expected, results[1])

    def assert_dicts_equal(self, expected, actual):
        for key, exp_value in expected.items():
            value = actual
            for fragment in key.split('.'):
                value = value[fragment]

            msg = 'Unexpected value for {} (expected {}, got {})'.format(
                key, exp_value, value
            )

            if isinstance(value, float):
                self.assertAlmostEqual(value, exp_value, msg=msg)
            else:
                self.assertEqual(value, exp_value, msg)

    def test_generate_sort_cmd(self):
        cmd = create_views.generate_sort_cmd(
            'vw__chemical_summary_by_ccg',
            ['processing_date', 'pct_id', 'chemical_id', 'items', 'cost', 'quantity'],
            '/tmp/vw__chemical_summary_by_ccg-2018-01-01-raw.csv',
            '/tmp/vw__chemical_summary_by_ccg-2018-01-01-sorted.csv',
        )
        exp_cmd = 'tail -n +2 {} | ionice -c 2 nice -n 10 sort {} -t, >> {}'.\
            format(
                '/tmp/vw__chemical_summary_by_ccg-2018-01-01-raw.csv',
                '-k3,3 -k2,2',
                '/tmp/vw__chemical_summary_by_ccg-2018-01-01-sorted.csv',
            )

        self.assertEqual(cmd, exp_cmd)
