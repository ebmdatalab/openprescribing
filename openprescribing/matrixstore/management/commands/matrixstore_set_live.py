"""
Updates the live version of the MatrixStore by updating the symlink at
MATRIXSTORE_LIVE_FILE. By default it searches for the most recently built
version of the most up-to-date file in MATRIXSTORE_BUILD_DIR (as determined by
the filename). If a date is supplied it restricts its search to files whose
timestamp (in the filename) matches that date.  If a filename is supplied it
will use that file.
"""
import os
import re

from django.conf import settings
from django.core.management import BaseCommand

from matrixstore.build.common import get_temp_filename


class Command(BaseCommand):
    help = __doc__

    def add_arguments(self, parser):
        parser.add_argument(
            '--date',
            help=(
                'Find the most recent file whose timestamp (in the filename) '
                'matches this date (YYYY-MM format)'
            )
        )
        parser.add_argument(
            '--filename',
            help="Don't search for files; just use this one"
        )

    def handle(self, date=None, filename=None, **kwargs):
        symlink = settings.MATRIXSTORE_LIVE_FILE
        if os.path.exists(symlink) and not os.path.islink(symlink):
            raise RuntimeError(
                'MATRIXSTORE_LIVE_FILE is not a symlink: {}'.format(symlink)
            )
        if filename:
            target_file = get_target_file(filename)
        else:
            target_file = get_most_recent_file(date)
        self.stdout.write(
            "Updating live symlink to: {}".format(target_file)
        )
        temp_file = get_temp_filename(symlink)
        os.symlink(target_file, temp_file)
        os.rename(temp_file, symlink)
        self.stdout.write(
            "NOTE: You will need to restart the application in order for this "
            "change to take effect"
        )


def get_target_file(filename):
    target_file = os.path.join(settings.MATRIXSTORE_BUILD_DIR, filename)
    if not os.path.exists(target_file):
        raise RuntimeError('No such file: {}'.format(target_file))
    # We want relative symlinks so they remain valid if we move the directory
    target_file = os.path.relpath(target_file, settings.MATRIXSTORE_BUILD_DIR)
    return target_file


def get_most_recent_file(date):
    candidates = [
        p for p in os.listdir(settings.MATRIXSTORE_BUILD_DIR)
        if re.match('matrixstore_\d{4}-\d{2}_.+\.sqlite', p)
    ]
    if date:
        date = date.replace('_', '-')
        candidates = [
            p for p in candidates
            if p.startswith('matrixstore_{}_'.format(date))
        ]
    if len(candidates) == 0:
        raise RuntimeError('No matching files found')
    return sorted(candidates)[-1]
