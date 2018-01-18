from distutils.dir_util import copy_tree
import os
import shutil

from django.core.management import BaseCommand, CommandError
from django.conf import settings
from django.test import override_settings

from django.core.management import call_command
from django.db import connection

from gcutils.bigquery import Client as BQClient, DATASETS
from gcutils.storage import Client as StorageClient
from frontend import bq_schemas as schemas
from frontend.models import MeasureValue, MeasureGlobal
from pipeline import runner


e2e_path = os.path.join(settings.SITE_ROOT, 'pipeline', 'e2e-test-data')


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        if os.environ['DJANGO_SETTINGS_MODULE'] != \
                'openprescribing.settings.test':
            raise CommandError('Command must run with test settings')

        with override_settings(
            PIPELINE_METADATA_DIR=os.path.join(
                settings.SITE_ROOT,
                'pipeline',
                'metadata'),
            PIPELINE_DATA_BASEDIR=os.path.join(e2e_path, 'data', ''),
            PIPELINE_IMPORT_LOG_PATH=os.path.join(e2e_path, 'log.json'),
        ):
            run_end_to_end()


def run_end_to_end():
    print('BQ_NONCE: {}'.format(settings.BQ_NONCE))

    num_measures = 56

    shutil.rmtree(settings.PIPELINE_DATA_BASEDIR)

    with open(settings.PIPELINE_IMPORT_LOG_PATH, 'w') as f:
        f.write('{}')

    for blob in StorageClient().bucket().list_blobs():
        blob.delete()

    for dataset_key in DATASETS:
        BQClient(dataset_key).create_dataset()

    client = BQClient('hscic')
    client.create_table('bnf', schemas.BNF_SCHEMA)
    client.create_table('ccgs', schemas.CCG_SCHEMA)
    client.create_table(
        'practice_statistics',
        schemas.PRACTICE_STATISTICS_SCHEMA
    )
    client.create_table('practices', schemas.PRACTICE_SCHEMA)
    client.create_table('prescribing', schemas.PRESCRIBING_SCHEMA)
    client.create_table('presentation', schemas.PRESENTATION_SCHEMA)
    client.create_table('tariff', schemas.TARIFF_SCHEMA)

    call_command('generate_presentation_replacements')

    with open('frontend/management/commands/replace_matviews.sql', 'r') as f:
        with connection.cursor() as c:
            c.execute(f.read())

    copy_tree(
        os.path.join(e2e_path, 'data-1'),
        os.path.join(e2e_path, 'data'),
    )

    runner.run_all(2017, 9, under_test=True)

    # We expect one MeasureGlobal per measure per month
    assert_count_equal(num_measures, MeasureGlobal)

    # We expect one MeasureValue for each CCG or Practice per measure per month
    assert_count_equal(6 * num_measures, MeasureValue)

    # We expect one statistic per CCG per month
    assert_raw_count_equal(2, 'vw__ccgstatistics')

    # We expect one chemical summary per CCG per month
    assert_raw_count_equal(2, 'vw__chemical_summary_by_ccg',
                           "chemical_id = '1001030C0'")

    # We expect one chemical summary per practice per month
    assert_raw_count_equal(4, 'vw__chemical_summary_by_practice',
                           "chemical_id = '1001030C0'")

    # We expect one summary per practice per month
    assert_raw_count_equal(4, 'vw__practice_summary')

    # We expect one presentation summary per month
    assert_raw_count_equal(1, 'vw__presentation_summary',
                           "presentation_code = '1001030C0AAAAAA'")

    # We expect one presentation summary per CCG per month
    assert_raw_count_equal(2, 'vw__presentation_summary_by_ccg',
                           "presentation_code = '1001030C0AAAAAA'")

    copy_tree(
        os.path.join(e2e_path, 'data-2'),
        os.path.join(e2e_path, 'data'),
    )

    runner.run_all(2017, 10, under_test=True)

    # We expect one MeasureGlobal per measure per month
    assert_count_equal(2 * num_measures, MeasureGlobal)

    # We expect one MeasureValue for each CCG or Practice per measure per month
    assert_count_equal(12 * num_measures, MeasureValue)

    # We expect one statistic per CCG per month
    assert_raw_count_equal(4, 'vw__ccgstatistics')

    # We expect one chemical summary per CCG per month
    assert_raw_count_equal(4, 'vw__chemical_summary_by_ccg',
                           "chemical_id = '1001030C0'")

    # We expect one chemical summary per practice per month
    assert_raw_count_equal(8, 'vw__chemical_summary_by_practice',
                           "chemical_id = '1001030C0'")

    # We expect one summary per practice per month
    assert_raw_count_equal(8, 'vw__practice_summary')

    # We expect one presentation summary per month
    assert_raw_count_equal(2, 'vw__presentation_summary',
                           "presentation_code = '1001030C0AAAAAA'")

    # We expect one presentation summary per CCG per month
    assert_raw_count_equal(4, 'vw__presentation_summary_by_ccg',
                           "presentation_code = '1001030C0AAAAAA'")


def assert_count_equal(expected, model):
    actual = model.objects.count()
    if actual != expected:
        msg = 'Expected {} {} objects, found {}'.format(
            expected, model, actual)
        raise CommandError(msg)


def assert_raw_count_equal(expected, table_name, where_condition=None):
    sql = 'SELECT COUNT(*) FROM {}'.format(table_name)
    if where_condition is not None:
        sql += ' WHERE {}'.format(where_condition)

    with connection.cursor() as c:
        c.execute(sql)
        results = c.fetchall()

    actual = results[0][0]

    if actual != expected:
        msg = 'Expected {} to return {}, got {}'.format(sql, expected, actual)
        raise CommandError(msg)
