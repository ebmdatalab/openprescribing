from multiprocessing.pool import Pool
import glob
import logging
import os
import subprocess
import tempfile
import traceback

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import connection

from common import utils
from gcutils.bigquery import Client, TableExporter
from frontend.models import ImportLog


logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """A command to create 'views' (actually ordinary tables) in postgres
    for subsets of data commonly requested over the API.

    Materialized views are too slow to build, so instead we generate
    the data in BigQuery and then load it into existing tables.

    The tables are not managed by Django so do not have models. They
    were created using the SQL at
    frontend/management/commands/replace_matviews.sql (also used by the tests).

    """
    def add_arguments(self, parser):
        parser.add_argument(
            '--view', help='view to update (default is to update all)')
        parser.add_argument(
            '--list-views', help='list available views', action='store_true')

    def handle(self, *args, **options):
        self.IS_VERBOSE = False
        if options['verbosity'] > 1:
            self.IS_VERBOSE = True

        base_path = os.path.join(
            settings.APPS_ROOT,
            'frontend',
            'management',
            'commands',
            'views_sql'
        )

        if options['view'] is not None:
            path = os.path.join(base_path), options['view'] + '.sql'
            self.view_paths = [path]
        else:
            self.view_paths = glob.glob(os.path.join(base_path, '*.sql'))

        if options['list_views']:
            self.list_views()
        else:
            self.fill_views()

    def list_views(self):
        for view in self.view_paths:
            print os.path.basename(view).replace('.sql', '')

    def fill_views(self):
        client = Client('hscic')

        pool = Pool(processes=len(self.view_paths))
        tables = []

        prescribing_date = ImportLog.objects.latest_in_category(
            'prescribing').current_at.strftime('%Y-%m-%d')

        for path in self.view_paths:
            table_name = "vw__%s" % os.path.basename(path).replace('.sql', '')
            table = client.get_table(table_name)
            tables.append(table)

            with open(path) as f:
                sql = f.read()

            substitutions = {'this_month': prescribing_date}
            args = [table.table_id, sql, substitutions]
            pool.apply_async(query_and_export, args)

        pool.close()
        pool.join()  # wait for all worker processes to exit

        for table in tables:
            self.download_and_import(table)
            self.log("-------------")

    def download_and_import(self, table):
        '''Download table from storage and import into local database.

        We sort the downloaded file with `sort` rather than in BigQuery,
        because we hit resource limits when we try to do so.  See #698 and #711
        for discussion.
        '''
        table_id = table.table_id
        storage_prefix = 'hscic/views/{}-'.format(table_id)
        exporter = TableExporter(table, storage_prefix)

        raw_file = tempfile.NamedTemporaryFile()
        raw_path = raw_file.name
        sorted_file = tempfile.NamedTemporaryFile()
        sorted_path = sorted_file.name

        self.log('Downloading {} to {}'.format(table_id, raw_path))
        exporter.download_from_storage_and_unzip(raw_file)

        self.log('Sorting {} to {}'.format(table_id, sorted_path))
        cmd = 'head -1 {} > {}'.format(raw_path, sorted_path)
        subprocess.check_call(cmd, shell=True)

        field_names = sorted_file.readline().strip().split(',')

        cmd = generate_sort_cmd(table_id, field_names, raw_path, sorted_path)
        subprocess.check_call(cmd, shell=True)

        copy_sql = "COPY {}({}) FROM STDIN WITH (FORMAT CSV)".format(
            table_id, ','.join(field_names))

        with connection.cursor() as cursor:
            with utils.constraint_and_index_reconstructor(table_id):
                self.log("Deleting from table %s..." % table_id)
                cursor.execute("DELETE FROM %s" % table_id)
                self.log("Copying CSV to %s..." % table_id)
                cursor.copy_expert(copy_sql, sorted_file)

        raw_file.close()
        sorted_file.close()

    def log(self, message):
        if self.IS_VERBOSE:
            logger.warn(message)
        else:
            logger.info(message)


def query_and_export(table_name, sql, substitutions):
    try:
        client = Client('hscic')
        table = client.get_table(table_name)

        storage_prefix = 'hscic/views/{}-'.format(table_name)
        logger.info("Generating view %s and saving to %s" % (
            table_name, storage_prefix))

        logger.info("Running SQL for %s: %s" % (table_name, sql))
        table.insert_rows_from_query(sql, substitutions=substitutions)

        exporter = TableExporter(table, storage_prefix)

        logger.info('Deleting existing data in storage at %s' % storage_prefix)
        exporter.delete_from_storage()

        logger.info('Exporting data to storage at %s' % storage_prefix)
        exporter.export_to_storage()

        logger.info("View generation complete for %s" % table_name)
    except Exception:
        # Log the formatted error, because the multiprocessing pool
        # this is called from only shows the error message (with no
        # traceback)
        logger.error(traceback.format_exc())
        raise


def generate_sort_cmd(table_name, field_names, raw_path, sorted_path):
    sort_keys = {
        'vw__ccgstatistics': ['pct_id'],
        'vw__chemical_summary_by_ccg': ['chemical_id', 'pct_id'],
        'vw__chemical_summary_by_practice': ['chemical_id', 'practice_id'],
        'vw__practice_summary': ['practice_id', 'processing_date'],
        'vw__presentation_summary': ['presentation_code', 'processing_date'],
        'vw__presentation_summary_by_ccg': ['presentation_code', 'pct_id'],
    }[table_name]
    sort_key_ixs = [field_names.index(k) + 1 for k in sort_keys]
    sort_opts = ' '.join('-k{},{}'.format(ix, ix) for ix in sort_key_ixs)
    # This won't work on OSX since no ionice is available.
    return 'tail -n +2 {} | ionice -c 2 nice -n 10 sort {} -t, >> {}'.format(
        raw_path, sort_opts, sorted_path)
