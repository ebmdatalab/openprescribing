import os

from django.conf import settings
from django.core.management.base import BaseCommand

from gcutils.bigquery import Client, build_schema
from google.cloud.exceptions import Conflict


class Command(BaseCommand):
    help = 'Creates or updates all BQ views that measures depend on'

    def handle(self, *args, **kwargs):
        base_path = os.path.join(settings.APPS_ROOT, 'frontend', 'management',
                                 'commands', 'measure_sql')

        client = Client("measures")

        for table_name in [
            'opioid_total_ome',
            'practice_data_all_low_priority',
            'pregabalin_total_mg',
            'vw__median_price_per_unit',
            'vw__ghost_generic_measure',
        ]:
            path = os.path.join(base_path, table_name + '.sql')
            with open(path, "r") as sql_file:
                sql = sql_file.read()

            try:
                client.create_table_with_view(table_name, sql, False)
            except Conflict:
                client.delete_table(table_name)
                client.create_table_with_view(table_name, sql, False)

        # cmpa_products is a table that has been created and managed by Rich.
        schema = build_schema(
            ('bnf_code', 'STRING'),
            ('bnf_name', 'STRING'),
            ('type', 'STRING'),
        )
        client.get_or_create_table('cmpa_products', schema)
