import logging
import os

from django.conf import settings
from django.core.management.base import BaseCommand
from frontend.bq_schemas import RAW_PRESCRIBING_SCHEMA_V1, RAW_PRESCRIBING_SCHEMA_V2
from gcutils.bigquery import Client, build_schema
from google.cloud.exceptions import Conflict

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Creates or updates all BQ views that measures depend on"

    def handle(self, *args, **kwargs):
        client = Client("hscic")

        try:
            client.create_storage_backed_table(
                "raw_prescribing_v1",
                RAW_PRESCRIBING_SCHEMA_V1,
                "hscic/prescribing_v1/20*Detailed_Prescribing_Information.csv",
            )
        except Conflict:
            pass

        try:
            client.create_storage_backed_table(
                "raw_prescribing_v2",
                RAW_PRESCRIBING_SCHEMA_V2,
                # This pattern may change once the data is published via the
                # new Open Data Portal.
                "hscic/prescribing_v2/20*.csv",
            )
        except Conflict:
            pass

        for table_name in [
            "all_prescribing",
            "normalised_prescribing",
            "normalised_prescribing_standard",
            "raw_prescribing_normalised",
        ]:
            self.recreate_table(client, table_name)

        client = Client("measures")

        for table_name in [
            "dmd_objs_with_form_route",
            "dmd_objs_hospital_only",
            "practice_data_all_low_priority",
            "vw__median_price_per_unit",
            "vw__opioids_total_dmd",
        ]:
            self.recreate_table(client, table_name)

        # cmpa_products is a table that has been created and managed by Rich.
        schema = build_schema(
            ("bnf_code", "STRING"), ("bnf_name", "STRING"), ("type", "STRING")
        )
        client.get_or_create_table("cmpa_products", schema)

    def recreate_table(self, client, table_name):
        logger.info("recreate_table: %s", table_name)
        base_path = os.path.join(
            settings.APPS_ROOT, "frontend", "management", "commands", "measure_sql"
        )

        path = os.path.join(base_path, table_name + ".sql")
        with open(path, "r") as sql_file:
            sql = sql_file.read()

        try:
            client.create_table_with_view(table_name, sql, False)
        except Conflict:
            client.delete_table(table_name)
            client.create_table_with_view(table_name, sql, False)
