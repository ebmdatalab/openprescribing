import sys

from django.conf import settings
from django.core.management import BaseCommand
from frontend.models import Measure
from gcutils.bigquery import Client


class Command(BaseCommand):
    def handle(self, measure_id, **options):
        if not options["delete_live_measure"]:
            if not measure_id.startswith(settings.MEASURE_PREVIEW_PREFIX):
                # We want these errors to be visble to users who run via bennettbot but the
                # only way to achieve that is to write them to stderr and exit 0 :(
                self.stdout.write(
                    f"Not deleting '{measure_id}' because it doesn't look like a "
                    f"preview measure (it doesn't start with "
                    f"'{settings.MEASURE_PREVIEW_PREFIX}')"
                )
                sys.exit(0)
        try:
            measure = Measure.objects.get(id=measure_id)
        except Measure.DoesNotExist:
            self.stdout.write(f"No measure with ID '{measure_id}'")
            sys.exit(0)
        delete_from_bigquery(measure_id)
        # The ON DELETE CASCADE configuration ensures that all MeasureValues are deleted
        # as well
        measure.delete()
        self.stdout.write(f"Deleted measure '{measure_id}'")

    def add_arguments(self, parser):
        parser.add_argument("measure_id")
        parser.add_argument("--delete-live-measure", action="store_true")


def delete_from_bigquery(measure_id):
    # Dataset name from `import_measures.MeasureCalculation.get_table()`
    client = Client("measures")
    # Table naming convention from `import_measures.MeasureCalculation.table_name()`
    table_suffix = f"_data_{measure_id}"

    tables_to_delete = [
        table for table in client.list_tables() if table.table_id.endswith(table_suffix)
    ]
    for table in tables_to_delete:
        client.delete_table(table.table_id)
