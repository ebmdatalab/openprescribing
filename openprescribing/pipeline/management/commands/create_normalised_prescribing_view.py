from django.core.management import BaseCommand
from gcutils.bigquery import Client
from google.cloud.exceptions import NotFound


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument(
            "--recreate",
            action="store_true",
            help="Delete views before recreating them",
        )

    def handle(self, *args, **kwargs):
        sql = """
        SELECT
          prescribing.sha AS sha,
          ccgs.regional_team_id AS regional_team,
          ccgs.stp_id AS stp,
          practices.ccg_id AS pct,
          prescribing.practice AS practice,
          TRIM(COALESCE(bnf_map.current_bnf_code, prescribing.bnf_code))
            AS bnf_code,
          prescribing.bnf_name AS bnf_name,
          prescribing.items AS items,
          prescribing.net_cost AS net_cost,
          prescribing.actual_cost AS actual_cost,
          prescribing.quantity AS quantity,
          prescribing.month AS month
        FROM
          {project}.{hscic}.prescribing AS prescribing
        LEFT JOIN
          {project}.{hscic}.bnf_map AS bnf_map
        ON
          bnf_map.former_bnf_code = prescribing.bnf_code
        INNER JOIN
          {project}.{hscic}.practices  AS practices
        ON practices.code = prescribing.practice
        INNER JOIN
          {project}.{hscic}.ccgs AS ccgs
        ON practices.ccg_id = ccgs.code
        """

        client = Client("hscic")

        if kwargs["recreate"]:
            try:
                client.delete_table("normalised_prescribing_standard")
            except NotFound:
                pass

        client.create_table_with_view(
            "normalised_prescribing_standard", sql, legacy=False
        )
