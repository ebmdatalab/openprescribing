"""
Runs the complete process to build a SQLite file with prescribing data in
MatrixStore format
"""
import os

from django.core.management import BaseCommand

from matrixstore.build.dates import DEFAULT_NUM_MONTHS
from matrixstore.build.init_db import init_db
from matrixstore.build.download_practice_stats import download_practice_stats
from matrixstore.build.import_practice_stats import import_practice_stats
from matrixstore.build.download_prescribing import download_prescribing
from matrixstore.build.import_prescribing import import_prescribing
from matrixstore.build.update_bnf_map import update_bnf_map


class Command(BaseCommand):
    help = __doc__

    def add_arguments(self, parser):
        parser.add_argument('end_date', help='YYYY-MM format')
        parser.add_argument('sqlite_path')
        parser.add_argument(
            '--months',
            help='Number of months of data to include (default: {})'.format(
                DEFAULT_NUM_MONTHS
            ),
            default=DEFAULT_NUM_MONTHS
        )

    def handle(self, end_date, sqlite_path, months=None, **kwargs):
        build(sqlite_path, end_date, months=months)


def build(sqlite_path, end_date, months=None):
    if not os.path.exists(sqlite_path):
        init_db(end_date, sqlite_path, months=months)
    download_practice_stats(end_date, months=months)
    import_practice_stats(sqlite_path)
    download_prescribing(end_date, months=months)
    import_prescribing(sqlite_path)
    update_bnf_map(sqlite_path)
