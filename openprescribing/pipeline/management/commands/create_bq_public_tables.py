"""Update tables in BQ public dataset."""


import glob
import os

from django.conf import settings
from django.core.management import BaseCommand

from gcutils.bigquery import Client


class Command(BaseCommand):
    help = __doc__

    def handle(self, *args, **kwargs):
        base_path = os.path.join(settings.APPS_ROOT, "bq_public_tables")

        client = Client("public")

        for path in glob.glob(os.path.join(base_path, "*.sql")):
            table_name = os.path.splitext(os.path.basename(path))[0]
            table = client.get_table(table_name)

            with open(path) as f:
                sql = f.read()

            table.insert_rows_from_query(sql)
