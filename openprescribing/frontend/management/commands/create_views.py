from multiprocessing.pool import Pool
import glob
import logging
import os
import traceback

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import connection

from common import utils
from ebmdatalab.bq_client import Client, TableExporter
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

    def handle(self, *args, **options):
        self.IS_VERBOSE = options['verbosity'] > 1

        prescribing_date = ImportLog.objects.latest_in_category(
            'prescribing').current_at.strftime('%Y-%m-%d')

        base_path = os.path.join(
            settings.SITE_ROOT,
            'frontend',
            'management',
            'commands',
            'views_sql'
        )

        dataset_name = settings.BQ_HSCIC_DATASET
        client = Client(dataset_name)

        pool = Pool()
        tables = []

        for path in glob.glob(os.path.join(base_path, '*.sql')):
            if options['view']:
                if os.path.basename(path) != options['view'] + '.sql':
                    continue
            table_name = "vw__%s" % os.path.basename(path).replace('.sql', '')
            table = client.get_table(table_name, reload=False)
            tables.append(table)

            # We do a string replacement here as we don't know how many
            # times a dataset substitution token (i.e. `{{dataset}}') will
            # appear in each SQL template. And we can't use new-style
            # formatting as some of the SQL has braces in.
            with open(path) as f:
                sql = f.read()
            sql = sql.replace('{{dataset}}', dataset_name)
            sql = sql.replace('{{this_month}}', prescribing_date)
            pool.apply_async(self.query_and_export, [table, sql])

        pool.close()
        pool.join()  # wait for all worker processes to exit

        for table in tables:
            self.download_and_import(table)

    def log(self, message):
        if self.IS_VERBOSE:
            logger.warn(message)
        else:
            logger.info(message)

    def query_and_export(self, table, sql):
        try:
            self.log("Running SQL for %s: %s" % (table.name, sql))
            table.insert_rows_from_query(sql)

            exporter = TableExporter(table, self.storage_prefix(table))

            self.log('Deleting existing data in storage at %s' % exporter.storage_prefix)
            exporter.delete_from_storage()

            self.log('Exporting data to storage at %s' % exporter.storage_prefix)
            exporter.export_to_storage()

        except Exception:
            # Log the formatted error, because the multiprocessing pool
            # this is called from only shows the error message (with no
            # traceback)
            self.log(traceback.format_exc())
            raise

    def download_and_import(self, table):
        exporter = TableExporter(table, self.storage_prefix(table))
        with exporter.download_from_storage_and_unzip() as f:
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

    def storage_prefix(self, table):
        return '{}/views/{}-'.format(table.dataset_name, table.name)
