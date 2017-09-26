from multiprocessing.pool import Pool
import datetime
import glob
import json
import logging
import os
import subprocess
import tempfile
import time
import traceback

from google.cloud import storage

from django.core.management.base import BaseCommand
from django.db import connection

from common import utils
from ebmdatalab import bigquery_old as bigquery
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
        self.fpath = os.path.dirname(__file__)
        self.view_paths = glob.glob(
            os.path.join(self.fpath, "./views_sql/*.sql"))
        self.view = None
        if options['list_views']:
            for view in self.view_paths:
                print os.path.basename(view).replace('.sql', '')
        else:
            if options['view']:
                self.view = options['view']
            self.fill_views()

    def fill_views(self):
        paths = []
        if self.view:
            for path in self.view_paths:
                if self.view in path:
                    paths.append(path)
                    break
        else:
            paths = self.view_paths
        pool = Pool(processes=len(paths))
        pool_results = []
        prescribing_date = ImportLog.objects.latest_in_category(
            'prescribing').current_at.strftime('%Y-%m-%d')
        for view in paths:
            if self.view and self.view not in view:
                continue

            tablename = "vw__%s" % os.path.basename(view).replace('.sql', '')

            # We do a string replacement here as we don't know how many
            # times a dataset substitution token (i.e. `{{dataset}}') will
            # appear in each SQL template. And we can't use new-style
            # formatting as some of the SQL has braces in.
            sql = open(view, "r").read().replace('{{dataset}}', self.dataset_name)
            sql = sql.replace("{{this_month}}", prescribing_date)

            result = pool.apply_async(
                query_and_export, [self.dataset_name, tablename, sql])
            pool_results.append(result)
        pool.close()
        pool.join()  # wait for all worker processes to exit
        for result in pool_results:
            tablename, gcs_uri = result.get()
            self.download_and_import(tablename, gcs_uri)
            self.log("-------------")

    def download_and_import(self, tablename, gcs_uri):
        client = Client(self.dataset_name)
        table = client.get_table_ref(tablename)
        storage_prefix = '{}/views/{}-'.format(self.dataset_name, table.name)
        exporter = TableExporter(table, storage_prefix)

        with tempfile.NamedTemporaryFile(mode='r+') as f:
            exporter.download_from_storage_and_unzip(f)
            f.seek(0)

            copy_str = "COPY %s(%s) FROM STDIN "
            copy_str += "WITH (FORMAT CSV)"
            fieldnames = f.readline().split(',')
            with connection.cursor() as cursor:
                with utils.constraint_and_index_reconstructor(tablename):
                    self.log("Deleting from table %s..." % tablename)
                    cursor.execute("DELETE FROM %s" % tablename)
                    self.log("Copying CSV to %s..." % tablename)
                    try:
                        cursor.copy_expert(copy_str % (
                            tablename, ','.join(fieldnames)), f)
                    except Exception:
                        import shutil
                        shutil.copyfile(f.name, "/tmp/error")
                        raise

    def log(self, message):
        if self.IS_VERBOSE:
            logger.warn(message)
        else:
            logger.info(message)


def query_and_export(dataset_name, tablename, sql):
    try:
        project_id = 'ebmdatalab'
        storage_prefix = '{}/views/{}-'.format(dataset_name, tablename)
        gzip_destination = "gs://ebmdatalab/{}*.csv.gz".format(storage_prefix)
        logger.info("Generating view %s and saving to %s" % (
            tablename, gzip_destination))

        client = Client(dataset_name)
        table = client.get_table_ref(tablename)

        logger.info("Running SQL for %s: %s" % (tablename, sql))
        table.insert_rows_from_query(sql)

        exporter = TableExporter(table, storage_prefix)

        logger.info('Deleting existing data in storage at %s' % exporter.storage_prefix)
        exporter.delete_from_storage()

        logger.info('Exporting data to storage at %s' % exporter.storage_prefix)
        exporter.export_to_storage()

        logger.info("View generation complete for %s" % tablename)
        return (tablename, gzip_destination)
    except Exception:
        # Log the formatted error, because the multiprocessing pool
        # this is called from only shows the error message (with no
        # traceback)
        logger.error(traceback.format_exc())
        raise
