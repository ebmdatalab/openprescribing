from django.conf import settings
from django.core.management import BaseCommand, CommandError

from frontend.models import Measure


class Command(BaseCommand):
    def handle(self, measure_id, **options):
        if not measure_id.startswith(settings.MEASURE_PREVIEW_PREFIX):
            raise CommandError(
                f"Not deleting '{measure_id}' because it doesn't look like a preview "
                f"measure (it doesn't start with '{settings.MEASURE_PREVIEW_PREFIX}')"
            )
        try:
            measure = Measure.objects.get(id=measure_id)
        except Measure.DoesNotExist:
            raise CommandError(f"No measure with ID '{measure_id}'")
        # The ON DELETE CASCADE configuration ensures that all MeasureValues are deleted
        # as well
        measure.delete()
        self.stdout.write(f"Deleted measure '{measure_id}'")

    def add_arguments(self, parser):
        parser.add_argument("measure_id")
