"""
Runs the complete process to build a SQLite file with prescribing data in
MatrixStore format and writes that file into `MATRIXSTORE_BUILD_DIR`
"""
import logging
import os

from django.conf import settings
from django.core.management import BaseCommand

from matrixstore.build.common import get_temp_filename
from matrixstore.build.dates import DEFAULT_NUM_MONTHS
from matrixstore.build.init_db import init_db
from matrixstore.build.download_practice_stats import download_practice_stats
from matrixstore.build.import_practice_stats import import_practice_stats
from matrixstore.build.download_prescribing import download_prescribing
from matrixstore.build.import_prescribing import import_prescribing
from matrixstore.build.update_bnf_map import update_bnf_map
from matrixstore.build.generate_filename import generate_filename


logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = __doc__

    def add_arguments(self, parser):
        parser.add_argument('end_date', help='YYYY-MM format')
        parser.add_argument(
            '--months',
            help='Number of months of data to include (default: {})'.format(
                DEFAULT_NUM_MONTHS
            ),
            default=DEFAULT_NUM_MONTHS
        )
        parser.add_argument(
            '--quiet',
            help="Don't emit logging output",
            action='store_true'
        )

    def handle(self, end_date, months=None, quiet=False, **kwargs):
        log_level = 'INFO' if not quiet else 'ERROR'
        with LogToStream('matrixstore', self.stdout, log_level):
            return build(end_date, months=months)


class LogToStream(object):
    """
    Context manager which captures messages sent to the named logger (and its
    children) and writes them to `stream`
    """

    def __init__(self, logger_name, stream, level):
        self.logger_name = logger_name
        self.stream = stream
        self.level = level

    def __enter__(self):
        self.logger = logging.getLogger(self.logger_name)
        self.handler = logging.StreamHandler(self.stream)
        formatter = logging.Formatter(
            fmt='[%(asctime)s] %(message)s',
            datefmt='%H:%M:%S'
        )
        self.handler.setFormatter(formatter)
        self.previous_level = self.logger.level
        self.logger.setLevel(self.level)
        self.logger.addHandler(self.handler)

    def __exit__(self, *args):
        self.logger.setLevel(self.previous_level)
        self.logger.removeHandler(self.handler)


def build(end_date, months=None):
    directory = settings.MATRIXSTORE_BUILD_DIR
    sqlite_temp = get_temp_filename(
        os.path.join(directory, 'matrixstore.sqlite')
    )
    init_db(end_date, sqlite_temp, months=months)
    download_practice_stats(end_date, months=months)
    import_practice_stats(sqlite_temp)
    download_prescribing(end_date, months=months)
    import_prescribing(sqlite_temp)
    update_bnf_map(sqlite_temp)
    basename = generate_filename(sqlite_temp)
    filename = os.path.join(directory, basename)
    logger.info('Moving file to final location: %s', filename)
    os.rename(sqlite_temp, filename)
    return filename
