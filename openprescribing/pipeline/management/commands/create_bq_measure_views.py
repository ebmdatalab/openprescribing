import logging
from pathlib import Path
from textwrap import dedent

from django.conf import settings
from django.core.management.base import BaseCommand
from frontend.bq_schemas import RAW_PRESCRIBING_SCHEMA_V1, RAW_PRESCRIBING_SCHEMA_V2
from gcutils.bigquery import Client
from google.cloud.exceptions import Conflict

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Creates or updates all BQ views that measures depend on"

    def handle(self, *args, **kwargs):
        create_prescribing_tables()
        create_measure_tables()


def create_prescribing_tables():
    """Create tables that contain prescribing data queried by all measures"""

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

    base_path = Path().joinpath(
        settings.APPS_ROOT, "frontend", "management", "commands", "measure_sql"
    )
    for table_name in [
        "all_prescribing",
        "normalised_prescribing",
        "normalised_prescribing_standard",
        "raw_prescribing_normalised",
    ]:
        recreate_table(client, base_path / f"{table_name}.sql")


def create_measure_tables():
    """Create tables that contain views on prescribing data for specific measures"""

    client = Client("measures")
    for path in (Path(settings.APPS_ROOT) / "measures" / "views").glob("vw__*.sql"):
        recreate_table(client, path)


def recreate_table(client, path):
    """Create or recreate a table based on SQL in file with given name"""

    table_name = path.stem
    logger.info("recreate_table: %s", table_name)
    sql = path.read_text()

    relpath = path.relative_to(Path(settings.APPS_ROOT))
    preamble = f"""\
    -- This SQL is checked in to the git repo at {relpath}.
    -- Do not make changes directly in BQ! Instead, change the version in the repo and run
    --
    --     ./manage.py create_bq_measure_views
    --
    """
    sql = dedent(preamble) + sql

    try:
        client.create_table_with_view(table_name, sql, False)
    except Conflict:
        client.delete_table(table_name)
        client.create_table_with_view(table_name, sql, False)
