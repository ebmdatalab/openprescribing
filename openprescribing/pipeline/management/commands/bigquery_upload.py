import datetime

from django.core.management import BaseCommand

from gcutils.bigquery import Client as BQClient
from gcutils.storage import Client as StorageClient
from frontend import models
from frontend import bq_schemas as schemas


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        update_bnf_table()

        client = BQClient("hscic")

        table = client.get_table("practices")
        table.insert_rows_from_pg(models.Practice, schemas.PRACTICE_SCHEMA)

        table = client.get_table("presentation")
        table.insert_rows_from_pg(
            models.Presentation,
            schemas.PRESENTATION_SCHEMA,
            transformer=schemas.presentation_transform,
        )

        table = client.get_table("practice_statistics")
        columns = [field.name for field in schemas.PRACTICE_STATISTICS_SCHEMA]
        columns[0] = "date"
        columns[-1] = "practice_id"
        table.insert_rows_from_pg(
            models.PracticeStatistics,
            schema=schemas.PRACTICE_STATISTICS_SCHEMA,
            columns=columns,
            transformer=schemas.statistics_transform,
        )

        sql = "SELECT MAX(month) FROM {hscic}.practice_statistics_all_years"
        results = client.query(sql)
        if results.rows[0][0] is None:
            last_uploaded_practice_statistics_date = datetime.date(1900, 1, 1)
        else:
            last_uploaded_practice_statistics_date = results.rows[0][0].date()

        table = client.get_table("practice_statistics_all_years")
        sql = """SELECT *
        FROM {hscic}.practice_statistics
        WHERE month > TIMESTAMP('{date}')"""
        substitutions = {"date": last_uploaded_practice_statistics_date}
        table.insert_rows_from_query(
            sql, write_disposition="WRITE_APPEND", substitutions=substitutions
        )

        table = client.get_table("pcns")
        table.insert_rows_from_pg(models.PCN, schemas.PCN_SCHEMA)

        table = client.get_table("ccgs")
        table.insert_rows_from_pg(
            models.PCT, schemas.CCG_SCHEMA, transformer=schemas.ccgs_transform
        )

        table = client.get_table("stps")
        table.insert_rows_from_pg(models.STP, schemas.STP_SCHEMA)

        table = client.get_table("regional_teams")
        table.insert_rows_from_pg(models.RegionalTeam, schemas.REGIONAL_TEAM_SCHEMA)

        date = models.ImportLog.objects.latest_in_category("prescribing").current_at
        table = client.get_table("prescribing_" + date.strftime("%Y_%m"))
        sql = """SELECT * FROM {hscic}.prescribing
        WHERE month = TIMESTAMP('{date}')"""
        substitutions = {"date": date}
        table.insert_rows_from_query(sql, substitutions=substitutions)


def update_bnf_table():
    """Update `bnf` table from cloud-stored CSV
    """
    storage_client = StorageClient()
    bucket = storage_client.get_bucket()
    blobs = bucket.list_blobs(prefix="hscic/bnf_codes/")
    blobs = sorted(blobs, key=lambda blob: blob.name, reverse=True)
    blob = blobs[0]

    bq_client = BQClient("hscic")
    table = bq_client.get_table("bnf")
    table.insert_rows_from_storage(blob.name, skip_leading_rows=1)
