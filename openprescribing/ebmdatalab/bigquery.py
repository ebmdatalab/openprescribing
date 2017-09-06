"""A random collection of methods used in openprescribing, in need of
refactoring, tests, and upgrading.

"""
from os import environ
import csv
import datetime
import json
import logging
import psycopg2
import re
import shutil
import subprocess
import tempfile
import time
import uuid

from google.cloud import bigquery
from google.cloud import storage
from google.cloud.bigquery import SchemaField
from google.cloud.exceptions import NotFound
from googleapiclient import discovery
from oauth2client.client import GoogleCredentials


logger = logging.getLogger(__name__)


DMD_SCHEMA = [
    SchemaField('dmdid', 'STRING'),
    SchemaField('bnf_code', 'STRING'),
    SchemaField('vpid', 'STRING'),
    SchemaField('display_name', 'STRING'),
    SchemaField('ema', 'STRING'),
    SchemaField('pres_statcd', 'STRING'),
    SchemaField('avail_restrictcd', 'STRING'),
    SchemaField('product_type', 'STRING'),
    SchemaField('non_availcd', 'STRING'),
    SchemaField('concept_class', 'STRING'),
    SchemaField('nurse_f', 'STRING'),
    SchemaField('dent_f', 'STRING'),
    SchemaField('prod_order_no', 'STRING'),
    SchemaField('sched_1', 'STRING'),
    SchemaField('sched_2', 'STRING'),
    SchemaField('padm', 'STRING'),
    SchemaField('fp10_mda', 'STRING'),
    SchemaField('acbs', 'STRING'),
    SchemaField('assort_flav', 'STRING'),
    SchemaField('catcd', 'STRING'),
    SchemaField('tariff_category', 'STRING'),
    SchemaField('flag_imported', 'STRING'),
    SchemaField('flag_broken_bulk', 'STRING'),
    SchemaField('flag_non_bioequivalence', 'STRING'),
    SchemaField('flag_special_containers', 'BOOLEAN')

]

CCG_SCHEMA = [
    SchemaField('code', 'STRING'),
    SchemaField('name', 'STRING'),
    SchemaField('ons_code', 'STRING'),
    SchemaField('org_type', 'STRING'),
    SchemaField('open_date', 'TIMESTAMP'),
    SchemaField('close_date', 'TIMESTAMP'),
    SchemaField('address', 'STRING'),
    SchemaField('postcode', 'STRING'),
]

PRESCRIBING_SCHEMA = [
    SchemaField('sha', 'STRING'),
    SchemaField('pct', 'STRING'),
    SchemaField('practice', 'STRING'),
    SchemaField('bnf_code', 'STRING'),
    SchemaField('bnf_name', 'STRING'),
    SchemaField('items', 'INTEGER'),
    SchemaField('net_cost', 'FLOAT'),
    SchemaField('actual_cost', 'FLOAT'),
    SchemaField('quantity', 'INTEGER'),
    SchemaField('month', 'TIMESTAMP'),
]

PRESENTATION_SCHEMA = [
    SchemaField('bnf_code', 'STRING'),
    SchemaField('name', 'STRING'),
    SchemaField('is_generic', 'BOOLEAN'),
    SchemaField('active_quantity', 'FLOAT'),
    SchemaField('adq', 'FLOAT'),
    SchemaField('adq_unit', 'STRING'),
    SchemaField('percent_of_adq', 'FLOAT'),
]

PRACTICE_SCHEMA = [
    SchemaField('code', 'STRING'),
    SchemaField('name', 'STRING'),
    SchemaField('address1', 'STRING'),
    SchemaField('address2', 'STRING'),
    SchemaField('address3', 'STRING'),
    SchemaField('address4', 'STRING'),
    SchemaField('address5', 'STRING'),
    SchemaField('postcode', 'STRING'),
    SchemaField('location', 'STRING'),
    SchemaField('ccg_id', 'STRING'),
    SchemaField('setting', 'INTEGER'),
    SchemaField('close_date', 'STRING'),
    SchemaField('join_provider_date', 'STRING'),
    SchemaField('leave_provider_date', 'STRING'),
    SchemaField('open_date', 'STRING'),
    SchemaField('status_code', 'STRING'),
]

PRACTICE_STATISTICS_SCHEMA = [
    SchemaField('month', 'TIMESTAMP'),
    SchemaField('male_0_4', 'INTEGER'),
    SchemaField('female_0_4', 'INTEGER'),
    SchemaField('male_5_14', 'INTEGER'),
    SchemaField('male_15_24', 'INTEGER'),
    SchemaField('male_25_34', 'INTEGER'),
    SchemaField('male_35_44', 'INTEGER'),
    SchemaField('male_45_54', 'INTEGER'),
    SchemaField('male_55_64', 'INTEGER'),
    SchemaField('male_65_74', 'INTEGER'),
    SchemaField('male_75_plus', 'INTEGER'),
    SchemaField('female_5_14', 'INTEGER'),
    SchemaField('female_15_24', 'INTEGER'),
    SchemaField('female_25_34', 'INTEGER'),
    SchemaField('female_35_44', 'INTEGER'),
    SchemaField('female_45_54', 'INTEGER'),
    SchemaField('female_55_64', 'INTEGER'),
    SchemaField('female_65_74', 'INTEGER'),
    SchemaField('female_75_plus', 'INTEGER'),
    SchemaField('total_list_size', 'INTEGER'),
    SchemaField('astro_pu_cost', 'FLOAT'),
    SchemaField('astro_pu_items', 'FLOAT'),
    SchemaField('star_pu', 'STRING'),
    SchemaField('pct_id', 'STRING'),
    SchemaField('practice', 'STRING')
]


def get_env_setting(setting, default=None):
    """ Get the environment setting.

    Return the default, or raise an exception if none supplied
    """
    try:
        return environ[setting]
    except KeyError:
        if default:
            return default
        else:
            error_msg = "Set the %s env variable" % setting
            raise StandardError(error_msg)


def get_bq_service():
    """Returns a bigquery service endpoint
    """
    # We've started using the google-cloud library since first writing
    # this. When it settles down a bit, start using that rather than
    # this low-level API. See
    # https://googlecloudplatform.github.io/google-cloud-python/
    credentials = GoogleCredentials.get_application_default()
    return discovery.build('bigquery', 'v2',
                           credentials=credentials)


def load_data_from_file(
        dataset_name, table_name,
        source_file_name, schema, _transform=None):
    """Given a CSV of data, load it into BigQuery using the specified
    schema, with an optional function to transform each row before
    loading.

    """
    # We use the new-style bigquery library here
    client = bigquery.Client(project='ebmdatalab')
    dataset = client.dataset(dataset_name)
    table = dataset.table(
        table_name,
        schema=schema)
    if not table.exists():
        table.create()
    table.reload()
    with tempfile.NamedTemporaryFile(mode='rb+') as csv_file:
        with open(source_file_name, 'rb') as source_file:
            writer = csv.writer(csv_file)
            reader = csv.reader(source_file)
            for row in reader:
                if _transform:
                    row = _transform(row)
                writer.writerow(row)
        job = table.upload_from_file(
            csv_file, source_format='text/csv',
            create_disposition="CREATE_IF_NEEDED",
            write_disposition="WRITE_TRUNCATE",
            rewind=True)
        try:
            wait_for_job(job)
        except Exception as e:
            shutil.copyfile(csv_file.name, "/tmp/error.csv")
            extra_info = '. Failed CSV has been copied to /tmp/error.csv; '
            extra_info += "first and last lines:\n"
            extra_info += subprocess.check_output(
                'head -1 /tmp/error.csv', shell=True)
            extra_info += subprocess.check_output(
                'tail -1 /tmp/error.csv', shell=True)
            e.args = (str(e.args[0]) + extra_info,), e.args[1:]
            raise
        return job


def prescribing_transform(row):
    """Transform a row from a formatted file into data suitable for
    storing in our bigquery schema


    A 'formatted file' is a file created by the
    import_hscic_prescribing Django management command.

    """
    # To match the prescribing table format in BigQuery, we have
    # to re-encode the date field as a bigquery TIMESTAMP and drop
    # a couple of columns
    row[10] = "%s 00:00:00" % row[10]
    del(row[3])
    del(row[-1])
    return row


def statistics_transform(row):
    """Transform a row from the frontend_practicestatistics table so it
    matches our statistics schema

    """
    row[0] = "%s 00:00:00" % row[0]  # BQ TIMESTAMP format
    return row


def presentation_transform(row):
    """Transform a row from the frontend_presentation table so it
    matches our statistics schema

    """
    if row[2] == 't':
        row[2] = 'true'
    else:
        row[2] = 'false'
    return row


def load_prescribing_data_from_file(
        dataset_name, table_name, source_file_name):
    """Given a formatted file of prescribing data, load it into BigQuery.
    """
    return load_data_from_file(
        dataset_name, table_name,
        source_file_name, PRESCRIBING_SCHEMA)


def load_statistics_from_pg(dataset='hscic'):
    """Load the frontend_stataistics table from the openprescribing
    application into BigQuery

    """
    schema = PRACTICE_STATISTICS_SCHEMA

    pg_cols = [x.name for x in schema]
    pg_cols[0] = 'date'
    pg_cols[-1] = 'practice_id'

    load_data_from_pg(
        dataset, 'practice_statistics', 'frontend_practicestatistics',
        schema, cols=pg_cols, _transform=statistics_transform)


def load_presentation_from_pg(dataset='hscic'):
    """Load the frontend_presentation table from the openprescribing
    application into BigQuery

    """
    load_data_from_pg(
        dataset, 'presentation', 'frontend_presentation',
        PRESENTATION_SCHEMA, _transform=presentation_transform)


def load_ccgs_from_pg(dataset='hscic'):
    """Load the frontend_practices table from the openprescribing
    application into BigQuery

    """
    def transform(row):
        if row[4]:
            row[4] = "%s 00:00:00" % row[4]
        if row[5]:
            row[5] = "%s 00:00:00" % row[5]
        return row

    load_data_from_pg(
        dataset, 'ccgs', 'frontend_pct',
        CCG_SCHEMA, cols=[x.name for x in CCG_SCHEMA], _transform=transform)


def load_data_from_pg(dataset_name, bq_table_name,
                      pg_table_name, schema, cols=None, _transform=None):
    """Loads every row currently in named postgres table to a
    specified table (with schema) in BigQuery

    """
    db_name = get_env_setting('DB_NAME')
    db_user = get_env_setting('DB_USER')
    db_pass = get_env_setting('DB_PASS')
    db_host = get_env_setting('DB_HOST', '127.0.0.1')
    conn = psycopg2.connect(database=db_name, user=db_user,
                            password=db_pass, host=db_host)
    with tempfile.NamedTemporaryFile(mode='r+b') as csv_file:
        if not cols:
            cols = [x.name for x in schema]
        sql = "COPY %s(%s) TO STDOUT (FORMAT CSV, NULL '')" % (
            pg_table_name, ",".join(cols))
        conn.cursor().copy_expert(
            sql, csv_file)
        csv_file.seek(0)
        load_data_from_file(
            dataset_name, bq_table_name,
            csv_file.name,
            schema,
            _transform
        )
        conn.commit()
        conn.close()


def wait_for_job(job):
    """Poll a BigQuery job until it is finished.

    Returns job
    """
    if job.state != 'RUNNING':
        job.begin()
    retry_count = 1000
    while retry_count > 0 and job.state != 'DONE':
        retry_count -= 1
        time.sleep(1)
        job.reload()
    assert not job.errors, job.errors
    return job


def download_from_gcs(gcs_uri, target_path):
    """Download file at given URI to `target_path
    """
    bucket, blob_name = gcs_uri.replace('gs://', '').split('/', 1)
    client = storage.Client(project='embdatalab')
    bucket = client.get_bucket(bucket)
    prefix = blob_name.split('*')[0]
    unzipped = open(target_path, 'w')
    cmd = "gunzip -c -f %s >> %s"
    for blob in bucket.list_blobs(prefix=prefix):
        with tempfile.NamedTemporaryFile(mode='rb+') as f:
            logger.info("Downloading %s to %s" % (blob.path, f.name))
            blob.chunk_size = 2 ** 30
            blob.download_to_file(f)
            f.flush()
            f.seek(0)
            subprocess.check_call(
                cmd % (f.name, unzipped.name), shell=True)
    return unzipped.name


def delete_from_gcs(gcs_uri):
    bucket, blob_name = gcs_uri.replace('gs://', '').split('/', 1)
    client = storage.Client(project='embdatalab')
    try:
        bucket = client.get_bucket(bucket)
        prefix = blob_name.split('*')[0]
        for blob in bucket.list_blobs(prefix=prefix):
            blob.delete()
    except NotFound:
        pass


def copy_table_to_gcs(table, gcs_uri):
    delete_from_gcs(gcs_uri)
    client = bigquery.client.Client(project='ebmdatalab')
    job = client.extract_table_to_storage(
        "extract-formatted-table-job-%s" % uuid.uuid1(), table,
        gcs_uri)
    job.destination_format = 'CSV'
    job.compression = 'GZIP'
    job.print_header = False
    job = wait_for_job(job)


def query_and_return(project_id, dataset_id, table_id, query, legacy=False):
    """Send query to BigQuery, wait, write it to table_id, and return
    response object when the job has completed.

    """
    if not legacy:
        # Rename any legacy-style table references to use standard
        # SQL dialect. Because we use a mixture of both, we
        # standardise on only using the legacy style for the time
        # being.
        query = re.sub(r'\[(.+?):(.+?)\.(.+?)\]', r'\1.\2.\3', query)
    payload = {
        "configuration": {
            "query": {
                "query": query,
                "flattenResuts": False,
                "allowLargeResults": True,
                "timeoutMs": 100000,
                "useQueryCache": True,
                "useLegacySql": legacy,
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
    # We've started using the google-cloud library since first
    # writing this. TODO: decide if we can use that throughout
    bq = get_bq_service()
    logger.info("Writing to bigquery table %s" % table_id)
    start = datetime.datetime.now()
    response = bq.jobs().insert(
        projectId=project_id,
        body=payload).execute()
    counter = 0
    job_id = response['jobReference']['jobId']
    while True:
        time.sleep(1)
        response = bq.jobs().get(
            projectId=project_id,
            jobId=job_id).execute()
        counter += 1
        if response['status']['state'] == 'DONE':
            if 'errors' in response['status']:
                query = str(response['configuration']['query']['query'])
                for i, l in enumerate(query.split("\n")):
                    # print SQL query with line numbers for debugging
                    print "{:>3}: {}".format(i + 1, l)
                raise StandardError(
                    json.dumps(response['status']['errors'], indent=2))
            else:
                break
    bytes_billed = float(
        response['statistics']['query']['totalBytesBilled'])
    gb_processed = round(bytes_billed / 1024 / 1024 / 1024, 2)
    est_cost = round(bytes_billed / 1e+12 * 5.0, 2)
    # Add our own metadata
    elapsed = (datetime.datetime.now() - start).total_seconds()
    response['openp'] = {'query': query,
                         'est_cost': est_cost,
                         'time': elapsed,
                         'gb_processed': gb_processed}
    logger.info("Time %ss, cost $%s" % (elapsed, est_cost))
    return response


def get_rows(project_id, dataset_id, table_name, max_results=None):
    """Iterate over the specified bigquery table, returning a dict for
    each row of data.

    """
    client = bigquery.Client(project=project_id)
    dataset = client.dataset(dataset_id)
    table = dataset.table(table_name)
    table.reload()
    fields = [x.name for x in table.schema]
    result = table.fetch_data(max_results=max_results)
    token = result.next_page_token
    while True:
        for row in result:
            yield _row_to_dict(row, fields)
        if token is None:
            break
        result = table.fetch_data(page_token=token, max_results=max_results)
        token = result.next_page_token
    raise StopIteration


def _row_to_dict(row, fields):
    """Convert a row from bigquery into a dictionary, and convert NaN to
    None

    """
    dict_row = {}
    for i, value in enumerate(row):
        key = fields[i]
        if value and str(value).lower() == 'nan':
            value = None
        dict_row[key] = value
    return dict_row
