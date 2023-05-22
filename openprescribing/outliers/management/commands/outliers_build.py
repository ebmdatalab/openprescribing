from django.core.management import BaseCommand
from outliers.build import build

DEFAULT_NUM_MONTHS = 6


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument("end_date", help="YYYY-MM format")
        parser.add_argument(
            "--months",
            help="Number of months of data to include (default: {})".format(
                DEFAULT_NUM_MONTHS
            ),
            default=DEFAULT_NUM_MONTHS,
        )

    def handle(self, end_date, months=None, **kwargs):
        return build(end_date, months)
