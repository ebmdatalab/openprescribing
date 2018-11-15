from django.core.management import BaseCommand, CommandError
from gcutils.bigquery import Client
from google.cloud.exceptions import Conflict


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        sql = """
        SELECT
          prescribing.sha AS sha,
          practices.ccg_id AS pct,
          prescribing.practice AS practice,
          COALESCE(bnf_map.current_bnf_code, prescribing.bnf_code)
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
        """

        client = Client('hscic')

        try:
            client.create_table_with_view(
                'normalised_prescribing_standard',
                sql,
                False
            )
        except Conflict:
            pass

        sql = sql.replace('{project}.', '{project}:')

        try:
            client.create_table_with_view(
                'normalised_prescribing_legacy',
                sql,
                legacy=True
            )
        except Conflict:
            pass
