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
from ebmdatalab import bigquery
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
        self.dataset = options.get('dataset', 'hscic')
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
            # Perform bigquery parts of operation in parallel
            result = pool.apply_async(
                query_and_export, [self.dataset, view, prescribing_date])
            pool_results.append(result)
        pool.close()
        pool.join()  # wait for all worker processes to exit
        for result in pool_results:
            tablename, gcs_uri = result.get()
            f = download_and_unzip(gcs_uri)
            copy_str = "COPY %s(%s) FROM STDIN "
            copy_str += "WITH (FORMAT CSV)"
            fieldnames = f.readline().split(',')
            with connection.cursor() as cursor:
                with utils.constraint_and_index_reconstructor(tablename):
                    self.log("Deleting from table...")
                    cursor.execute("DELETE FROM %s" % tablename)
                    self.log("Copying CSV to postgres...")
                    try:
                        cursor.copy_expert(copy_str % (
                            tablename, ','.join(fieldnames)), f)
                    except Exception:
                        import shutil
                        shutil.copyfile(f.name, "/tmp/error")
                        raise
            f.close()
            self.log("-------------")

    def log(self, message):
        if self.IS_VERBOSE:
            logger.warn(message)
        else:
            logger.info(message)


# BigQuery helper functions. Candidates for moving to
# ebmdatalab-python.

def query_and_export(dataset, view, prescribing_date):
    try:
        project_id = 'ebmdatalab'
        tablename = "vw__%s" % os.path.basename(view).replace('.sql', '')
        gzip_destination = "gs://ebmdatalab/%s/views/%s-*.csv.gz" % (
            dataset, tablename)
        # We do a string replacement here as we don't know how many
        # times a dataset substitution token (i.e. `{{dataset}}') will
        # appear in each SQL template. And we can't use new-style
        # formatting as some of the SQL has braces in.
        sql = open(view, "r").read().replace('{{dataset}}', dataset)
        sql = sql.replace("{{this_month}}", prescribing_date)
        print sql
        # Execute query and wait
        job_id = query_and_return(
            project_id, dataset, tablename, sql)
        logger.info("Awaiting query completion")
        wait_for_job(job_id, project_id)

        # Export to GCS and wait
        job_id = export_to_gzip(
            project_id, dataset, tablename, gzip_destination)
        logger.info("Awaiting export completion")
        wait_for_job(job_id, project_id)
        return (tablename, gzip_destination)
    except Exception:
        # Log the formatted error, because the multiprocessing pool
        # this is called from only shows the error message (with no
        # traceback)
        logger.error(traceback.format_exc())
        raise


def download_and_unzip(gcs_uri):
    # Download from GCS
    unzipped = tempfile.NamedTemporaryFile(mode='r+')
    for i, f in enumerate(download_from_gcs(gcs_uri)):
        # Unzip
        if i == 0:
            cmd = "zcat -f %s >> %s"
        else:
            # When the file is split into several shards in GCS, it
            # puts a header on every file, so we have to skip that
            # header on all except the first shard.
            cmd = "zcat -f %s | tail -n +2 >> %s"
        subprocess.check_call(
            cmd % (f.name, unzipped.name), shell=True)
    return unzipped


def export_to_gzip(project_id, dataset_id, table_id, destination):
    payload = {
        "configuration": {
            "extract": {
                "compression": 'GZIP',
                "destinationFormat": 'CSV',
                "destinationUri": destination,
                "printHeader": True,
                "sourceTable": {
                    "datasetId": dataset_id,
                    "projectId": project_id,
                    "tableId": table_id
                }
            }
        }
    }
    return insert_job(project_id, payload)


def download_from_gcs(gcs_uri):
    bucket, blob_name = gcs_uri.replace('gs://', '').split('/', 1)
    client = storage.Client(project='embdatalab')
    bucket = client.get_bucket(bucket)
    prefix = blob_name.split('*')[0]
    for blob in bucket.list_blobs(prefix=prefix):
        with tempfile.NamedTemporaryFile(mode='rb+') as f:
            logger.info("Downloading %s to %s" % (blob.path, f.name))
            blob.download_to_file(f)
            f.flush()
            f.seek(0)
            yield f


def query_and_return(project_id, dataset_id, table_id, query):
    """Send query to BigQuery, wait, write it to table_id, and return
    response object when the job has completed.

    """
    payload = {
        "configuration": {
            "query": {
                "query": query,
                "flattenResuts": False,
                "allowLargeResults": True,
                "timeoutMs": 100000,
                "useQueryCache": True,
                "useLegacySql": False,
                "destinationTable": {
                    "projectId": project_id,
                    "tableId": table_id,
                    "datasetId": dataset_id
                },
                "createDisposition": "CREATE_IF_NEEDED",
                "writeDisposition": "WRITE_TRUNCATE"
            }
        }
    }
    logging.info("Writing to bigquery table %s" % table_id)
    return insert_job(project_id, payload)


def insert_job(project_id, payload):
    bq = bigquery.get_bq_service()
    response = bq.jobs().insert(
        projectId=project_id,
        body=payload).execute()
    return response['jobReference']['jobId']


def wait_for_job(job_id, project_id):
    bq = bigquery.get_bq_service()
    start = datetime.datetime.now()
    counter = 0
    while True:
        time.sleep(1)
        response = bq.jobs().get(
            projectId=project_id,
            jobId=job_id).execute()
        counter += 1
        if response['status']['state'] == 'DONE':
            if 'errors' in response['status']:
                error = json.dumps(response['status']['errors'], indent=2)
                if 'query' in response['configuration']:
                    query = str(response['configuration']['query']['query'])
                    for i, l in enumerate(query.split("\n")):
                        # print SQL query with line numbers for debugging
                        logging.error(
                            error + ":\n" + "{:>3}: {}".format(i + 1, l))
                raise StandardError(error)
            else:
                break
    elapsed = (datetime.datetime.now() - start).total_seconds()
    if 'query' in response['statistics']:
        bytes_billed = float(
            response['statistics']['query']['totalBytesBilled'])
        gb_processed = round(bytes_billed / 1024 / 1024 / 1024, 2)
        est_cost = round(bytes_billed / 1e+12 * 5.0, 2)
        # Add our own metadata
        response['openp'] = {'est_cost': est_cost,
                             'time': elapsed,
                             'gb_processed': gb_processed}
    else:
        est_cost = 'n/a'
    logging.warn("Time %ss, cost $%s" % (elapsed, est_cost))
    return response
