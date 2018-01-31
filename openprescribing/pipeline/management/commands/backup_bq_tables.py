import re

from django.conf import settings
from django.core.management import BaseCommand

from gcutils.bigquery import Client, TableExporter
from gcutils.storage import Client as StorageClient


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        self.backup_table('prescribing')
        self.backup_table('practice_statistics')

    def backup_table(self, table_name):
        client = Client('hscic')
        sql = 'SELECT max(month) FROM {hscic}.%s' % table_name
        latest_date = client.query(sql).rows[0][0]
        latest_year_and_month = latest_date.strftime('%Y_%m')
        table = client.get_table(table_name)

        storage_client = StorageClient()
        bucket = storage_client.bucket()
        year_and_months = set()

        prefix_base = 'backups/{}/'.format(table_name)

        for blob in bucket.list_blobs(prefix=prefix_base):
            match = re.search('/(\d{4}_\d{2})-', blob.name)
            year_and_months.add(match.groups()[0])

        if latest_year_and_month in year_and_months:
            print '{} table already backed up for {}'. \
                format(table_name, latest_year_and_month)
            return

        storage_prefix = '{}/{}/{}-'.format(
            prefix_base, latest_year_and_month, table_name)
        exporter = TableExporter(table, storage_prefix)
        exporter.export_to_storage()
