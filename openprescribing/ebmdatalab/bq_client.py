from contextlib import contextmanager
import csv
import os
import re
import subprocess
import tempfile
import time
import uuid

from google.cloud import bigquery as gcbq
from google.cloud import storage as gcs
from google.cloud.exceptions import Conflict

from django.conf import settings
from django.db import connection

from openprescribing.utils import mkdir_p


class Client(object):
    def __init__(self, dataset_name):
        # TODO: pass in credentials, rather than inferring from environment
        # TODO: get this from settings
        self.gcbq_client = gcbq.Client(project='ebmdatalab')
        self.dataset = self.gcbq_client.dataset(dataset_name)

    def list_jobs(self):
        return self.gcbq_client.list_jobs()

    def create_dataset(self):
        self.dataset.create()

    def delete_dataset(self):
        self.dataset.delete()

    def create_table(self, table_name, schema):
        table = self.dataset.table(table_name, schema)
        table.create()
        return Table(table)

    def get_table(self, table_name, reload=True):
        table = self.dataset.table(table_name)
        if reload:
            table.reload()
        return Table(table)

    def get_or_create_table(self, table_name, schema):
        try:
            table = self.create_table(table_name, schema)
        except Conflict:
            table = self.get_table(table_name)
        return table

    def query(self, sql, legacy=False, **options):
        if not legacy:
            sql = convert_legacy_table_names(sql)

        query = self.gcbq_client.run_sync_query(sql)
        set_options(query, options)

        query.run()

        # The call to .run() might return before results are actually ready.
        # See # https://cloud.google.com/bigquery/docs/reference/rest/v2/jobs/query#timeoutMs
        wait_for_job(query.job)

        return query


class Table(object):
    def __init__(self, gcbq_table):
        self.gcbq_table = gcbq_table
        self.gcbq_client = gcbq_table._dataset._client
        # TODO don't hardcode this
        self.gcs_client = gcs.Client(project='ebmdatalab')
        self.bucket = self.gcs_client.bucket('ebmdatalab')
        self.name = gcbq_table.name
        self.dataset_name = gcbq_table._dataset.name

    def fetch_data(self):
        return self.gcbq_table.fetch_data()

    def insert_rows_from_query(self, sql, legacy=False, **options):
        if not legacy:
            sql = convert_legacy_table_names(sql)

        default_options = {
            'useLegacySql': legacy,
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

    def export_to_storage(self, **options):
        default_options = {
            'compression': 'GZIP',
        }

        destination_uri = 'gs://ebmdatalab/{}/views/{}-*.csv.gz'.format(
            self.dataset_name,
            self.name,
        )

        job = self.gcbq_client.extract_table_to_storage(
            options.pop('job_name', gen_job_name()),
            self.gcbq_table,
            destination_uri,
        )

        set_options(job, options, default_options)

        job.begin()

        wait_for_job(job)

    @property
    def storage_prefix(self):
        return '{}/views/{}-'.format(self.dataset_name, self.name)

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

    @contextmanager
    def download_from_storage_and_unzip(self):
        with tempfile.NamedTemporaryFile(mode='r+') as f_unzipped:
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
                    cmd % (f_zipped.name, f_unzipped.name), shell=True)

            yield f_unzipped

    def delete_from_storage(self):
        for blob in self.storage_blobs():
            blob.delete()


class BQModelTable(object):
    '''Represents a table in BQ that mirrors table of ORM model.

    Subclasses should define class attributes:

        * table_name
        * fields
        * model
    '''

    def get_table(self):
        client = Client(settings.BQ_HSCIC_DATASET)
        return client.get_table(self.table_name)

    # def create_table(self):
    #     # TODO

    def insert_rows_from_csv(self, path):
        table = self.get_table()
        table.insert_rows_from_csv(path)

    @contextmanager
    def dump_rows_from_pg(self):
        sql = "COPY %s(%s) TO STDOUT (FORMAT CSV, NULL '')" % (
            self.pg_table_name, ','.join(self.pg_columns))

        with tempfile.NamedTemporaryFile(mode='r+b') as f:
            with connection.cursor() as c:
                c.copy_expert(sql, f)
            f.seek(0)
            yield f

    def insert_rows_from_pg(self):
        with self.dump_rows_from_pg() as f1:
            with tempfile.NamedTemporaryFile(mode='r+b') as f2:
                reader = csv.reader(f1)
                writer = csv.writer(f2)
                for row in reader:
                    writer.writerow(self.pg_to_bq_transform(row))
                f2.seek(0)
                self.insert_rows_from_csv(f2.name)

    @property
    def pg_table_name(self):
        return self.model._meta.db_table

    @property
    def pg_columns(self):
        return [f[0] for f in self.fields]

    @staticmethod
    def pg_to_bq_transform(row):
        return row


def wait_for_job(job, timeout_s=3600):
    t0 = time.time()

    # Would like to use `while not job.done():` but cannot until we upgrade
    # version of g.c.bq.
    while True:
        job.reload()
        if job.state == 'DONE':
            break

        if time.time() - t0 > timeout_s:
            raise TimeoutError
        time.sleep(1)

    if job.errors is not None:
        raise JobError(job.errors)

    # TODO Log time and cost


class TimeoutError(StandardError):
    pass


class JobError(StandardError):
    pass


def convert_legacy_table_names(sql):
    return re.sub(r'\[(.+?):(.+?)\.(.+?)\]', r'\1.\2.\3', sql)


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
