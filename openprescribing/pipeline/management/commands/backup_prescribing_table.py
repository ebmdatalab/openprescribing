import re

from django.conf import settings
from django.core.management import BaseCommand

from google.cloud import storage as gcs

from gcutils.bigquery import Client, TableExporter


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        client = Client(settings.BQ_HSCIC_DATASET)
        sql = 'SELECT max(month) FROM hscic.prescribing'
        latest_date = client.query(sql).rows[0][0]
        latest_year_and_month = latest_date.strftime('%Y_%m')
        table = client.get_table('prescribing')

        storage_client = gcs.Client(project=table.project_name)
        bucket = storage_client.bucket(table.project_name)
        year_and_months = set()

        prefix_base = 'prescribing/prescribing_backups/'

        for blob in bucket.list_blobs(prefix=prefix_base):
            match = re.search('{}/(\d{4}_\d{2})-'.format(prefix_base),
                              blob.name)
            year_and_months.add(match.groups()[0])

        if latest_year_and_month in year_and_months:
            print 'Prescribing table already backed up for {}'. \
                format(latest_year_and_month)
            return

        year_and_months = sorted(year_and_months)

        num_to_keep = 5

        if len(year_and_months) > num_to_keep:
            for year_and_month in year_and_months[:-num_to_keep]:
                prefix = '{}/{}'.format(prefix_base, year_and_month)
                for blob in bucket.list_blobs(prefix=prefix):
                    blob.delete()

        storage_prefix = '{}/{}-'.format(prefix_base, latest_year_and_month)
        exporter = TableExporter(table, storage_prefix)
        exporter.export_to_storage()
