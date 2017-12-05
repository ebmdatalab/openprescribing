from __future__ import print_function

from collections import defaultdict
import string
import subprocess
import tempfile
import time
import uuid

from google.cloud import bigquery as gcbq
from google.cloud.exceptions import Conflict, NotFound

import pandas as pd

from django.conf import settings

from gcutils.storage import Client as StorageClient
from gcutils.table_dumper import TableDumper


DATASETS = {
    'hscic': settings.BQ_HSCIC_DATASET,
    'measures': settings.BQ_MEASURES_DATASET,
    'tmp_eu': settings.BQ_TMP_EU_DATASET,
}


try:
    DATASETS['test'] = settings.BQ_TEST_DATASET
except AttributeError:
    pass


class Client(object):
    def __init__(self, dataset_key=None):
        self.project_name = settings.BQ_PROJECT

        # gcbq expects an environment variable called
        # GOOGLE_APPLICATION_CREDENTIALS whose value is the path of a JSON file
        # containing the credentials to access Google Cloud Services.
        self.gcbq_client = gcbq.Client(project=self.project_name)

        if dataset_key is None:
            self.dataset_name = None
            self.dataset = None
        else:
            self.dataset_name = DATASETS[dataset_key]
            self.dataset = self.gcbq_client.dataset(self.dataset_name)

    def list_jobs(self):
        return self.gcbq_client.list_jobs()

    def create_dataset(self):
        self.dataset.location = settings.BQ_LOCATION
        self.dataset.default_table_expiration_ms = settings.BQ_DEFAULT_TABLE_EXPIRATION_MS
        self.dataset.create()

    def delete_dataset(self):
        for table in self.dataset.list_tables():
            table.delete()
        self.dataset.delete()

    def create_table(self, table_name, schema):
        table = self.dataset.table(table_name, schema)

        try:
            table.create()
        except NotFound as e:
            assert 'Not found: Dataset' in str(e)
            self.create_dataset()
            table.create()

        return Table(table, self.project_name)

    def get_table(self, table_name):
        table = self.dataset.table(table_name)
        return Table(table, self.project_name)

    def get_or_create_table(self, table_name, schema):
        try:
            table = self.create_table(table_name, schema)
        except Conflict:
            table = self.get_table(table_name)
        return table

    def create_storage_backed_table(self, table_name, schema, gcs_path):
        gcs_client = StorageClient()
        bucket = gcs_client.bucket()
        if bucket.get_blob(gcs_path) is None:
            raise RuntimeError('Could not find blob at {}'.format(gcs_path))

        gcs_uri = 'gs://{}/{}'.format(self.project_name, gcs_path)

        resource = {
            'tableReference': {'tableId': table_name},
            'externalDataConfiguration': {
                'csvOptions': {'skipLeadingRows': '1'},
                'sourceFormat': 'CSV',
                'sourceUris': [gcs_uri],
                'schema': {'fields': schema}
            }
        }

        path = '/projects/{}/datasets/{}/tables'.format(
            self.project_name,
            self.dataset_name
        )

        try:
            self.gcbq_client._connection.api_request(
                method='POST',
                path=path,
                data=resource
            )
        except NotFound as e:
            assert 'Not found: Dataset' in str(e)
            self.create_dataset()
            self.gcbq_client._connection.api_request(
                method='POST',
                path=path,
                data=resource
            )

        return self.get_table(table_name)

    def create_table_with_view(self, table_name, sql, legacy):
        assert '{project}' in sql
        sql = interpolate_sql(sql, project=self.project_name)
        table = self.dataset.table(table_name)
        table.view_query = sql
        table.view_use_legacy_sql = legacy
        try:
            table.create()
        except NotFound as e:
            assert 'Not found: Dataset' in str(e)
            self.create_dataset()
            table.create()
        return Table(table, self.project_name)

    def query(self, sql, legacy=False, **options):
        sql = interpolate_sql(sql)
        query = self.gcbq_client.run_sync_query(sql)
        set_options(query, options)
        query.use_legacy_sql = legacy

        query.run()

        # The call to .run() might return before results are actually ready.
        # See https://cloud.google.com/bigquery/docs/reference/rest/v2/jobs/query#timeoutMs
        wait_for_job(query.job)

        return query

    def query_into_dataframe(self, sql, legacy=False):
        sql = interpolate_sql(sql)
        kwargs = {
            'project_id': self.project_name,
            'verbose': False,
            'dialect': 'legacy' if legacy else 'standard',
        }
        try:
            return pd.read_gbq(sql, **kwargs)
        except:
            for n, line in enumerate(sql.splitlines()):
                print(n + 1, line)
            raise


class Table(object):
    def __init__(self, gcbq_table, project_name):
        self.gcbq_table = gcbq_table
        self.gcbq_client = gcbq_table._dataset._client
        self.project_name = project_name
        self.name = gcbq_table.name
        self.dataset_name = gcbq_table._dataset.name

    @property
    def qualified_name(self):
        return '{}.{}'.format(self.dataset_name, self.name)

    def get_rows(self):
        self.gcbq_table.reload()
        return self.gcbq_table.fetch_data()

    def get_rows_as_dicts(self):
        self.gcbq_table.reload()
        field_names = [field.name for field in self.gcbq_table.schema]

        for row in self.get_rows():
            yield row_to_dict(row, field_names)

    def insert_rows_from_query(self, sql, substitutions=None, legacy=False, **options):
        substitutions = substitutions or {}
        sql = interpolate_sql(sql, **substitutions)
        default_options = {
            'use_legacy_sql': legacy,
            'allow_large_results': True,
            'write_disposition': 'WRITE_TRUNCATE',
            'destination': self.gcbq_table,
        }

        job = self.gcbq_client.run_async_query(
            options.pop('job_name', gen_job_name()),
            sql
        )
        set_options(job, options, default_options)

        job.begin()

        wait_for_job(job)

    def insert_rows_from_csv(self, csv_path, **options):
        default_options = {
            'source_format': 'text/csv',
            'write_disposition': 'WRITE_TRUNCATE',
        }

        merge_options(options, default_options)

        with open(csv_path, 'rb') as f:
            # This starts a job, so we don't need to call job.begin()
            job = self.gcbq_table.upload_from_file(f, **options)

        wait_for_job(job)

    def insert_rows_from_pg(self, model, columns, transformer=None):
        table_dumper = TableDumper(model, columns, transformer)

        with tempfile.NamedTemporaryFile() as f:
            table_dumper.dump_to_file(f)
            f.seek(0)
            self.insert_rows_from_csv(f.name)

    def insert_rows_from_storage(self, gcs_path, **options):
        default_options = {
            'write_disposition': 'WRITE_TRUNCATE',
        }

        gcs_uri = 'gs://{}/{}'.format(self.project_name, gcs_path)

        job = self.gcbq_client.load_table_from_storage(
            gen_job_name(),
            self.gcbq_table, gcs_uri
        )

        set_options(job, options, default_options)

        job.begin()

        wait_for_job(job)

    def delete_all_rows(self, **options):
        sql = 'DELETE FROM {} WHERE true'.format(self.qualified_name)

        default_options = {
            'use_legacy_sql': False,
        }

        job = self.gcbq_client.run_async_query(gen_job_name(), sql)

        set_options(job, options, default_options)

        job.begin()

        wait_for_job(job)


class TableExporter(object):
    def __init__(self, table, storage_prefix):
        self.table = table
        self.storage_prefix = storage_prefix
        storage_client = StorageClient()
        self.bucket = storage_client.bucket()

    def export_to_storage(self, **options):
        default_options = {
            'compression': 'GZIP',
        }

        destination_uri = 'gs://{}/{}*.csv.gz'.format(
            self.table.project_name,
            self.storage_prefix,
        )

        job = self.table.gcbq_client.extract_table_to_storage(
            options.pop('job_name', gen_job_name()),
            self.table.gcbq_table,
            destination_uri,
        )

        set_options(job, options, default_options)

        job.begin()

        wait_for_job(job)

    def storage_blobs(self):
        for blob in self.bucket.list_blobs(prefix=self.storage_prefix):
            yield blob

    def download_from_storage(self):
        for blob in self.storage_blobs():
            with tempfile.NamedTemporaryFile(mode='rb+') as f:
                blob.download_to_file(f)
                f.flush()
                f.seek(0)
                yield f

    def download_from_storage_and_unzip(self, f_out):
        for i, f_zipped in enumerate(self.download_from_storage()):
            # Unzip
            if i == 0:
                cmd = "gunzip -c -f %s >> %s"
            else:
                # When the file is split into several shards in GCS, it
                # puts a header on every file, so we have to skip that
                # header on all except the first shard.
                cmd = "gunzip -c -f %s | tail -n +2 >> %s"
            subprocess.check_call(
                cmd % (f_zipped.name, f_out.name), shell=True)

    def delete_from_storage(self):
        for blob in self.storage_blobs():
            blob.delete()


def wait_for_job(job, timeout_s=3600):
    t0 = time.time()

    # Would like to use `while not job.done():` but cannot until we upgrade
    # version of g.c.bq.
    while True:
        job.reload()
        if job.state == 'DONE':
            break

        if time.time() - t0 > timeout_s:
            msg = 'Timeout waiting for job {} after {} second'.format(
                job.name, timeout_s
            )
            raise TimeoutError(msg)

        time.sleep(1)

    if job.errors is not None:
        raise JobError(job.errors)


class TimeoutError(StandardError):
    pass


class JobError(StandardError):
    pass


def set_options(thing, options, default_options=None):
    if default_options is not None:
        merge_options(options, default_options)
    for k, v in options.items():
        setattr(thing, k, v)


def merge_options(options, default_options):
    for k, v in default_options.items():
        options.setdefault(k, v)


def gen_job_name():
    return uuid.uuid4().hex


def row_to_dict(row, field_names):
    """Convert a row from bigquery into a dictionary, and convert NaN to
    None

    """
    dict_row = {}
    for value, field_name in zip(row, field_names):
        if value and str(value).lower() == 'nan':
            value = None
        dict_row[field_name] = value
    return dict_row


def results_to_dicts(results):
    field_names = [field.name for field in results.schema]
    for row in results.rows:
        yield row_to_dict(row, field_names)


def build_schema(*fields):
    return [gcbq.SchemaField(*field) for field in fields]


class SafeDict(dict):
    def __missing__(self, key):
        return '{' + key + '}'


def interpolate_sql(sql, **substitutions):
    '''Interpolates substitutions (plus datasets) into given SQL.

    Many of our SQL queries contain template variables, because the names of
    certain tables or fields are generated at runtime, and because each test
    run uses different dataset names.  This function replaces template
    variables with the corresponding values in substitutions, or with the
    dataset name.

    >>> interpolate_sql('SELECT {col} from {hscic}.table', col='c')
    'SELECT c from hscic_12345.table'

    Since the values of some substitutions (esp. those from import_measures)
    themselves contain template variables, we do the interpolation twice.

    Use of the SafeDict allows us to do interpolation when the SQL contains
    things in curly braces that shoudn't be interpolated (for instance, JS
    functions defined in SQL).
    '''
    substitutions.update(DATASETS)
    sql = string.Formatter().vformat(sql, (), SafeDict(**substitutions))
    sql = string.Formatter().vformat(sql, (), SafeDict(**substitutions))
    return sql
