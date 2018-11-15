from django.core.management import BaseCommand, CommandError
from gcutils.bigquery import Client
from google.cloud.exceptions import Conflict, NotFound


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument(
            '--recreate', action='store_true',
            help='Delete views before recreating them'
        )

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

        for table_name, legacy in [
            ('normalised_prescribing_legacy', True),
            ('normalised_prescribing_standard', False),
        ]:

            if kwargs['recreate']:
                try:
                    client.delete_table(table_name)
                except NotFound:
                    pass

            client.create_table_with_view(table_name, sql, legacy)
