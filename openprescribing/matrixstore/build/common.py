import errno
import os
import os.path
import tempfile

from django.conf import settings


def get_practice_stats_filename(date):
    """
    Return the full path to the practice statistics CSV file for this date
    """
    return _get_filename(date, 'practice_stats')


def get_prescribing_filename(date):
    """
    Return the full path to the prescribing CSV file this date
    """
    return _get_filename(date, 'prescribing')


def get_filename_for_download(remote_filename):
    """
    Given the name of a file on Google Cloud Storage return the full local path
    to which this file should be downloaded
    """
    return os.path.join(
        settings.MATRIXSTORE_IMPORT_DIR,
        'temporary_downloads',
        os.path.basename(remote_filename)
    )


def get_temp_filename(filename):
    """
    Return the name of a temporary file in the same directory as the supplied
    file
    """
    directory, basename = os.path.split(filename)
    _ensure_dir_exists(directory)
    # We want to return the name of the file without actually creating it as
    # sometimes we use this to create a new SQLite file and SQLite will
    # complain if the file already exists
    return '{directory}/.tmp.{random}.{basename}'.format(
        directory=directory,
        basename=basename,
        random=next(tempfile._get_candidate_names())
    )


def _get_filename(date, type_name):
    return os.path.join(
        settings.MATRIXSTORE_IMPORT_DIR,
        '{}_{}.csv.gz'.format(date, type_name)
    )


def _ensure_dir_exists(directory):
    try:
        os.makedirs(directory)
    except OSError as e:
        if e.errno != errno.EEXIST:
            raise
