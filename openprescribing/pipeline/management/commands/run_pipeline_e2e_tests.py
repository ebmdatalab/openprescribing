from distutils.dir_util import copy_tree
import glob
import os
import shutil

from django.core.management import BaseCommand, CommandError
from django.conf import settings

from django.core.management import call_command
from django.db import connection

from gcutils.bigquery import Client as BQClient, DATASETS, build_schema
from gcutils.storage import Client as StorageClient
from frontend import bq_schemas as schemas
from frontend.models import MeasureValue, MeasureGlobal
from dmd.models import NCSOConcession, DMDProduct, TariffPrice, DMDVmpp
from openprescribing.slack import notify_slack
from pipeline import runner


e2e_path = os.path.join(settings.APPS_ROOT, 'pipeline', 'e2e-test-data')


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        if os.environ['DJANGO_SETTINGS_MODULE'] != \
                'openprescribing.settings.e2etest':
            raise CommandError('Command must run with e2etest settings')

        try:
            run_end_to_end()
        except Exception:
            msg = 'End-to-end test failed (seed: %s)\n\n' % settings.BQ_NONCE
            msg += 'Check logs in /tmp/'
            notify_slack(msg)
            raise

        msg = 'Pipeline tests ran to completion (seed: %s)' % settings.BQ_NONCE
        notify_slack(msg)


def run_end_to_end():
    print('BQ_NONCE: {}'.format(settings.BQ_NONCE))

    call_command('migrate')

    path = os.path.join(settings.APPS_ROOT, 'frontend', 'management',
                        'commands', 'measure_definitions')

    # No MeasureGlobals or MeasureValues are generated for the ghost branded
    # generics measure, because both numerator and denominator are computed
    # from a view (vw__ghost_generic_measure) which has no data.  Rather than
    # populate this view, it is simpler to pretend it doesn't exist.
    num_measures = len(os.listdir(path)) - 1

    shutil.rmtree(settings.PIPELINE_DATA_BASEDIR, ignore_errors=True)

    with open(settings.PIPELINE_IMPORT_LOG_PATH, 'w') as f:
        f.write('{}')

    for blob in StorageClient().bucket().list_blobs():
        blob.delete()

    for dataset_key in DATASETS:
        BQClient(dataset_key).create_dataset()

    client = BQClient('hscic')
    client.create_table('bnf', schemas.BNF_SCHEMA)
    client.create_table('ccgs', schemas.CCG_SCHEMA)
    client.create_table('ppu_savings', schemas.PPU_SAVING_SCHEMA)
    client.create_table(
        'practice_statistics',
        schemas.PRACTICE_STATISTICS_SCHEMA
    )
    client.create_table(
        'practice_statistics_all_years',
        schemas.PRACTICE_STATISTICS_SCHEMA
    )
    client.create_table('practices', schemas.PRACTICE_SCHEMA)
    client.create_table('prescribing', schemas.PRESCRIBING_SCHEMA)
    client.create_table('presentation', schemas.PRESENTATION_SCHEMA)
    client.create_table('tariff', schemas.TARIFF_SCHEMA)
    client.create_table('bdz_adq', schemas.BDZ_ADQ_SCHEMA)

    client = BQClient('measures')
    # This is enough of a schema to allow the practice_data_all_low_priority
    # table to be created, since it references these fields.  Once populated by
    # import_measures, the tables in the measures dataset will have several
    # more fields.  But we don't need to specify exactly what they are, as BQ
    # will work it out when the data is inserted with insert_rows_from_query.
    measures_schema = build_schema(
        ('month', 'DATE'),
        ('practice_id', 'STRING'),
        ('numerator', 'INTEGER'),
        ('denominator', 'INTEGER'),
    )
    path = os.path.join(settings.APPS_ROOT, 'frontend', 'management',
                        'commands', 'measure_definitions', '*.json')
    for path in glob.glob(path):
        measure_id = os.path.splitext(os.path.basename(path))[0]
        client.create_table('practice_data_' + measure_id, measures_schema)
        client.create_table('ccg_data_' + measure_id, measures_schema)
        client.create_table('global_data_' + measure_id, measures_schema)

    # Although there are no model instances, we call upload_model to create the
    # tables in BQ that might be required by certain measure views.
    client = BQClient('dmd')
    client.upload_model(NCSOConcession)
    client.upload_model(DMDProduct)
    client.upload_model(TariffPrice)
    client.upload_model(DMDVmpp)

    call_command('generate_presentation_replacements')

    path = os.path.join(settings.APPS_ROOT, 'frontend', 'management',
                        'commands', 'replace_matviews.sql')
    with open(path) as f:
        with connection.cursor() as c:
            c.execute(f.read())

    copy_tree(
        os.path.join(e2e_path, 'data-1'),
        os.path.join(e2e_path, 'data'),
    )

    runner.run_all(2017, 9, under_test=True)

    # We expect one MeasureGlobal per measure per month.
    assert_count_equal(num_measures, MeasureGlobal)

    # We expect one MeasureValue for each organisation per measure per month
    # (There are 4 practices, 2 CCGs, 2 STPs, and 2 regional teams).
    assert_count_equal(10 * num_measures, MeasureValue)

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

    # We expect one MeasureValue for each organisation per measure per month
    assert_count_equal(20 * num_measures, MeasureValue)

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
