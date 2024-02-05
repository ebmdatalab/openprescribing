"""Update measure tables in BQ public dataset."""

import os

from django.conf import settings
from django.core.management import BaseCommand
from frontend.models import Measure
from gcutils.bigquery import Client

from openprescribing.utils import partially_format


class Command(BaseCommand):
    help = __doc__

    def add_arguments(self, parser):
        parser.add_argument("--measure_ids", nargs="+")

    def handle(self, *args, measure_ids, **kwargs):
        base_path = os.path.join(settings.APPS_ROOT, "bq_public_tables")

        client = Client("public")

        with open(os.path.join(base_path, "_measure_template.sql")) as f:
            measure_template_sql = f.read()

        if measure_ids:
            measures = Measure.objects.filter(id__in=measure_ids)
        else:
            measures = Measure.objects.all()

        for measure in measures:
            table_name = "measure_" + measure.id
            print(table_name)
            table = client.get_table(table_name)

            numerator_sql = """
            SELECT
                CAST(month AS DATE) AS month,
                practice AS practice_id,
                {numerator_columns}
            FROM {numerator_from}
            WHERE {numerator_where}
            GROUP BY month, practice_id
            """.format(
                numerator_columns=measure.numerator_columns,
                numerator_from=measure.numerator_from,
                numerator_where=measure.numerator_where,
            )

            denominator_sql = """
            SELECT
                CAST(month AS DATE) AS month,
                practice AS practice_id,
                {denominator_columns}
            FROM {denominator_from}
            WHERE {denominator_where}
            GROUP BY month, practice_id
            """.format(
                denominator_columns=measure.denominator_columns,
                denominator_from=measure.denominator_from,
                denominator_where=measure.denominator_where,
            )

            sql = partially_format(
                measure_template_sql,
                numerator_sql=numerator_sql,
                denominator_sql=denominator_sql,
            )

            table.insert_rows_from_query(sql)
