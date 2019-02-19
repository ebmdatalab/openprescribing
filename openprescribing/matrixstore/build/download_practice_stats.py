"""
Downloads practice statistics data from BigQuery into the "matrixstore_import"
directory inside `settings.PIPELINE_DATA_BASEDIR`
"""
import csv
import gzip
import logging
import os

from gcutils.bigquery import Client

from .common import get_practice_stats_filename, get_temp_filename
from .dates import generate_dates


logger = logging.getLogger(__name__)


def download_practice_stats(end_date, months=None):
    for date in generate_dates(end_date, months=months):
        ensure_stats_downloaded_for_date(date)


def ensure_stats_downloaded_for_date(date):
    """
    Download practice statistics for date, or do nothing if already downloaded
    """
    filename = get_practice_stats_filename(date)
    if os.path.exists(filename):
        return
    logger.info('Downloading practice statistics for %s', date)
    temp_name = get_temp_filename(filename)
    result = Client('hscic').query(
        """
        SELECT *
        FROM {hscic}.practice_statistics_all_years
        WHERE month = TIMESTAMP("%s")
        """
        % (date,)
    )
    with gzip.open(temp_name, 'wb') as f:
        writer = csv.writer(f)
        writer.writerow(result.field_names)
        for row in result.rows:
            writer.writerow(row)
    os.rename(temp_name, filename)
