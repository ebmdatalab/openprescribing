from multiprocessing.pool import Pool
import glob
import logging
import os
import tempfile
import traceback

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import connection

from common import utils
from ebmdatalab.bigquery import Client, TableExporter
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
        self.dataset_name = options.get('dataset', 'hscic')

        base_path = os.path.join(
            settings.SITE_ROOT,
            'frontend',
            'management',
            'commands',
            'views_sql'
        )

        if options['view'] is not None:
            self.view_paths = [os.path.join(base_path), options['view'] + '.sql']
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
        client = Client(self.dataset_name)

        pool = Pool(processes=len(self.view_paths))
        tables = []

        prescribing_date = ImportLog.objects.latest_in_category(
            'prescribing').current_at.strftime('%Y-%m-%d')

        for path in self.view_paths:
            table_name = "vw__%s" % os.path.basename(path).replace('.sql', '')
            table = client.get_table_ref(table_name)
            tables.append(table)

            # We do a string replacement here as we don't know how many
            # times a dataset substitution token (i.e. `{{dataset}}') will
            # appear in each SQL template. And we can't use new-style
            # formatting as some of the SQL has braces in.
            with open(path) as f:
                sql = f.read()
            sql = sql.replace('{{dataset}}', self.dataset_name)
            sql = sql.replace('{{this_month}}', prescribing_date)
            pool.apply_async(query_and_export, [table, sql])

        pool.close()
        pool.join()  # wait for all worker processes to exit

        for table in tables:
            self.download_and_import(table)
            self.log("-------------")

    def download_and_import(self, table):
        storage_prefix = '{}/views/{}-'.format(self.dataset_name, table.name)
        exporter = TableExporter(table, storage_prefix)

        with tempfile.NamedTemporaryFile(mode='r+') as f:
            exporter.download_from_storage_and_unzip(f)
            f.seek(0)

            field_names = f.readline()
            copy_sql = "COPY %s(%s) FROM STDIN WITH (FORMAT CSV)" % (table.name, field_names)

            with connection.cursor() as cursor:
                with utils.constraint_and_index_reconstructor(table.name):
                    self.log("Deleting from table %s..." % table.name)
                    cursor.execute("DELETE FROM %s" % table.name)

                    self.log("Copying CSV to %s..." % table.name)
                    try:
                        cursor.copy_expert(copy_sql, f)
                    except Exception:
                        import shutil
                        shutil.copyfile(f.name, "/tmp/error")
                        raise

    def log(self, message):
        if self.IS_VERBOSE:
            logger.warn(message)
        else:
            logger.info(message)


def query_and_export(dataset_name, table, sql):
    try:
        storage_prefix = '{}/views/{}-'.format(dataset_name, table.name)
        logger.info("Generating view %s and saving to %s" % (
            table.name, storage_prefix))

        logger.info("Running SQL for %s: %s" % (table.name, sql))
        table.insert_rows_from_query(sql)

        exporter = TableExporter(table, storage_prefix)

        logger.info('Deleting existing data in storage at %s' % exporter.storage_prefix)
        exporter.delete_from_storage()

        logger.info('Exporting data to storage at %s' % exporter.storage_prefix)
        exporter.export_to_storage()

        logger.info("View generation complete for %s" % table.name)
    except Exception:
        # Log the formatted error, because the multiprocessing pool
        # this is called from only shows the error message (with no
        # traceback)
        logger.error(traceback.format_exc())
        raise
