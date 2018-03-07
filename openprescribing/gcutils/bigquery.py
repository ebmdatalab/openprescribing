from __future__ import print_function

import string
import subprocess
import tempfile

from google.cloud import bigquery as gcbq
from google.cloud.exceptions import Conflict, NotFound

import pandas as pd

from django.conf import settings
from django.db.models import fields as model_fields
from django.db.models.fields import related as related_fields

from gcutils.storage import Client as StorageClient
from gcutils.table_dumper import TableDumper


DATASETS = {
    'hscic': settings.BQ_HSCIC_DATASET,
    'measures': settings.BQ_MEASURES_DATASET,
    'tmp_eu': settings.BQ_TMP_EU_DATASET,
    'dmd': settings.BQ_DMD_DATASET,
}


try:
    DATASETS['test'] = settings.BQ_TEST_DATASET
except AttributeError:
    pass


class Client(object):
    def __init__(self, dataset_key=None):
        self.project = settings.BQ_PROJECT

        # gcbq expects an environment variable called
        # GOOGLE_APPLICATION_CREDENTIALS whose value is the path of a JSON file
        # containing the credentials to access Google Cloud Services.
        self.gcbq_client = gcbq.Client(project=self.project)

        self.dataset_key = dataset_key

        if dataset_key is None:
            self.dataset_id = None
            self.dataset = None
        else:
            self.dataset_id = DATASETS[dataset_key]
            dataset_ref = self.gcbq_client.dataset(self.dataset_id)
            self.dataset = gcbq.Dataset(dataset_ref)

    def run_job(self, method_name, args, config_opts, config_default_opts):
        job_config = {
            'extract_table': gcbq.ExtractJobConfig,
            'load_table_from_file': gcbq.LoadJobConfig,
            'load_table_from_uri': gcbq.LoadJobConfig,
            'query': gcbq.QueryJobConfig,
        }[method_name]()

        for k, v in config_default_opts.items():
            setattr(job_config, k, v)
        for k, v in config_opts.items():
            setattr(job_config, k, v)

        method = getattr(self.gcbq_client, method_name)
        job = method(*args, job_config=job_config)
        return job.result()

    def list_jobs(self):
        return self.gcbq_client.list_jobs()

    def create_dataset(self):
        self.dataset.location = settings.BQ_LOCATION
        self.dataset.default_table_expiration_ms =\
            settings.BQ_DEFAULT_TABLE_EXPIRATION_MS
        self.gcbq_client.create_dataset(self.dataset)

    def delete_dataset(self):
        for table_list_item in self.gcbq_client.list_tables(self.dataset):
            self.gcbq_client.delete_table(table_list_item.reference)
        self.gcbq_client.delete_dataset(self.dataset)

    def create_table(self, table_id, schema):
        table_ref = self.dataset.table(table_id)
        table = gcbq.Table(table_ref, schema=schema)

        try:
            self.gcbq_client.create_table(table)
        except NotFound as e:
            if 'Not found: Dataset' not in str(e):
                raise
            self.create_dataset()
            self.gcbq_client.create_table(table)

        return Table(table_ref, self)

    def get_table(self, table_id):
        table_ref = self.dataset.table(table_id)
        return Table(table_ref, self)

    def get_or_create_table(self, table_id, schema):
        try:
            table = self.create_table(table_id, schema)
        except Conflict:
            table = self.get_table(table_id)
        return table

    def create_storage_backed_table(self, table_id, schema, gcs_path):
        gcs_client = StorageClient()
        bucket = gcs_client.bucket()
        if bucket.get_blob(gcs_path) is None:
            raise RuntimeError('Could not find blob at {}'.format(gcs_path))

        gcs_uri = 'gs://{}/{}'.format(self.project, gcs_path)

        resource = {
            'tableReference': {'tableId': table_id},
            'externalDataConfiguration': {
                'csvOptions': {'skipLeadingRows': '1'},
                'sourceFormat': 'CSV',
                'sourceUris': [gcs_uri],
                'schema': {'fields': schema}
            }
        }

        path = '/projects/{}/datasets/{}/tables'.format(
            self.project,
            self.dataset_id
        )

        try:
            self.gcbq_client._connection.api_request(
                method='POST',
                path=path,
                data=resource
            )
        except NotFound as e:
            if 'Not found: Dataset' not in str(e):
                raise
            self.create_dataset()
            self.gcbq_client._connection.api_request(
                method='POST',
                path=path,
                data=resource
            )

        return self.get_table(table_id)

    def create_table_with_view(self, table_id, sql, legacy):
        assert '{project}' in sql
        sql = interpolate_sql(sql, project=self.project)
        table_ref = self.dataset.table(table_id)
        table = gcbq.Table(table_ref)
        table.view_query = sql
        table.view_use_legacy_sql = legacy

        try:
            self.gcbq_client.create_table(table)
        except NotFound as e:
            if 'Not found: Dataset' not in str(e):
                raise
            self.create_dataset()
            self.gcbq_client.create_table(table)

        return Table(table_ref, self)

    def query(self, sql, legacy=False, **options):
        default_options = {
            'use_legacy_sql': legacy,
        }
        args = [interpolate_sql(sql)]
        iterator = self.run_job('query', args, options, default_options)
        return Results(iterator)

    def query_into_dataframe(self, sql, legacy=False):
        sql = interpolate_sql(sql)
        kwargs = {
            'project_id': self.project,
            'verbose': False,
            'dialect': 'legacy' if legacy else 'standard',
        }
        try:
            return pd.read_gbq(sql, **kwargs)
        except:
            for n, line in enumerate(sql.splitlines()):
                print(n + 1, line)
            raise

    def upload_model(self, model, table_id=None):
        if table_id is None:
            table_id = model._meta.db_table
            if self.dataset_key == 'dmd':
                assert table_id.startswith('dmd_')
                table_id = table_id[4:]
        schema = build_schema_from_model(model)
        table = self.get_or_create_table(table_id, schema)
        columns = [
            f.db_column or f.attname
            for f in model._meta.fields
            if not f.auto_created
        ]
        timestamp_ixs = [
            ix
            for ix, field in enumerate(schema)
            if field.field_type == 'TIMESTAMP'
        ]

        def transformer(record):
            for ix in timestamp_ixs:
                record[ix] = record[ix] + ' 00:00:00'
            return record

        table.insert_rows_from_pg(model, columns, transformer)


class Table(object):
    def __init__(self, gcbq_table_ref, client):
        self.gcbq_table_ref = gcbq_table_ref
        self.client = client

        self.gcbq_client = client.gcbq_client
        try:
            self.get_gcbq_table()
        except NotFound:
            self.gcbq_table = None

        self.table_id = gcbq_table_ref.table_id
        self.dataset_id = gcbq_table_ref.dataset_id
        self.project = gcbq_table_ref.project

    @property
    def qualified_name(self):
        return '{}.{}'.format(self.dataset_id, self.table_id)

    def run_job(self, *args):
        return self.client.run_job(*args)

    def get_gcbq_table(self):
        self.gcbq_table = self.gcbq_client.get_table(self.gcbq_table_ref)

    def get_rows(self):
        if self.gcbq_table is None:
            self.get_gcbq_table()

        for row in self.gcbq_client.list_rows(self.gcbq_table):
            yield row.values()

    def get_rows_as_dicts(self):
        if self.gcbq_table is None:
            self.get_gcbq_table()

        field_names = [field.name for field in self.gcbq_table.schema]

        for row in self.get_rows():
            yield row_to_dict(row, field_names)

    def insert_rows_from_query(self, sql, substitutions=None, legacy=False,
                               **options):
        default_options = {
            'use_legacy_sql': legacy,
            'allow_large_results': True,
            'write_disposition': 'WRITE_TRUNCATE',
            'destination': self.gcbq_table_ref,
        }

        substitutions = substitutions or {}
        sql = interpolate_sql(sql, **substitutions)

        args = [sql]
        self.run_job('query', args, options, default_options)

    def insert_rows_from_csv(self, csv_path, **options):
        default_options = {
            'source_format': 'text/csv',
            'write_disposition': 'WRITE_TRUNCATE',
        }

        with open(csv_path, 'rb') as f:
            args = [f, self.gcbq_table_ref]
            self.run_job('load_table_from_file', args, options,
                         default_options)

    def insert_rows_from_pg(self, model, columns, transformer=None):
        table_dumper = TableDumper(model, columns, transformer)

        with tempfile.NamedTemporaryFile() as f:
            table_dumper.dump_to_file(f)
            f.seek(0)
            self.insert_rows_from_csv(f.name, foo='bar')

    def insert_rows_from_storage(self, gcs_path, **options):
        default_options = {
            'write_disposition': 'WRITE_TRUNCATE',
        }

        gcs_uri = 'gs://{}/{}'.format(self.project, gcs_path)

        args = [gcs_uri, self.gcbq_table_ref]
        self.run_job('load_table_from_uri', args, options, default_options)

    def export_to_storage(self, storage_prefix, **options):
        default_options = {
            'compression': 'GZIP',
        }

        destination_uri = 'gs://{}/{}*.csv.gz'.format(
            self.project,
            storage_prefix,
        )

        args = [self.gcbq_table, destination_uri]
        self.run_job('extract_table', args, options, default_options)

    def delete_all_rows(self, **options):
        default_options = {
            'use_legacy_sql': False,
        }

        sql = 'DELETE FROM {} WHERE true'.format(self.qualified_name)

        args = [sql]
        self.run_job('query', args, options, default_options)


class Results(object):
    def __init__(self, gcbq_row_iterator):
        self.gcbq_row_iterator = gcbq_row_iterator

    @property
    def rows(self):
        for row in self.gcbq_row_iterator:
            yield row.values()


class TableExporter(object):
    def __init__(self, table, storage_prefix):
        self.table = table
        self.storage_prefix = storage_prefix
        storage_client = StorageClient()
        self.bucket = storage_client.bucket()

    def export_to_storage(self, **options):
        self.table.export_to_storage(self.storage_prefix, **options)

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


def build_schema_from_model(model):
    field_mappings = {
        model_fields.BigIntegerField: 'INTEGER',
        model_fields.CharField: 'STRING',
        model_fields.DateField: 'TIMESTAMP',
        model_fields.FloatField: 'FLOAT',
        model_fields.IntegerField: 'INTEGER',
        model_fields.NullBooleanField: 'BOOLEAN',
        model_fields.TextField: 'STRING',
        related_fields.ForeignKey: 'INTEGER',
    }

    fields = [
        (f.name, field_mappings[type(f)])
        for f in model._meta.fields
        if not f.auto_created
    ]

    return build_schema(*fields)


class InterpolationDict(dict):
    def __missing__(self, key):
        return '{' + key + '}'


def interpolate_sql(sql, **substitutions):
    '''Interpolates substitutions (plus datasets defined in DATASETS) into
    given SQL.

    Many of our SQL queries contain template variables, because the names of
    certain tables or fields are generated at runtime, and because each test
    run uses different dataset names.  This function replaces template
    variables with the corresponding values in substitutions, or with the
    dataset name.

    >>> interpolate_sql('SELECT {col} from {hscic}.table', col='c')
    'SELECT c from hscic_12345.table'

    Since the values of some substitutions (esp. those from import_measures)
    themselves contain template variables, we do the interpolation twice.

    Use of the InterpolationDict allows us to do interpolation when the SQL
    contains things in curly braces that shoudn't be interpolated (for
    instance, JS functions defined in SQL).
    '''
    substitutions.update(DATASETS)
    substitutions = InterpolationDict(**substitutions)
    sql = string.Formatter().vformat(sql, (), substitutions)
    sql = string.Formatter().vformat(sql, (), substitutions)
    return sql
