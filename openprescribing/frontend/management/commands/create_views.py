from __future__ import print_function
import logging

from django.core.management.base import BaseCommand
from django.db import connection

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    "A command to refresh our materialized views in Postgres"

    def add_arguments(self, parser):
        parser.add_argument(
            '--view', help='view to refresh (default is to refresh all)')
        parser.add_argument(
            '--list-views', help='list available views', action='store_true')

    def handle(self, *args, **options):
        self.IS_VERBOSE = False
        if options['verbosity'] > 1:
            self.IS_VERBOSE = True

        self.materialized_views = [
            'vw__medians_for_tariff',
        ]

        if options['view'] is not None:
            if options['view'] not in self.materialized_views:
                raise ValueError('Unknown view: {}'.format(options['view']))
            else:
                self.materialized_views = [options['view']]

        if options['list_views']:
            self.list_views()
        else:
            self.fill_views()

    def list_views(self):
        for view in self.materialized_views:
            print(view)

    def fill_views(self):
        with connection.cursor() as cursor:
            for view_id in self.materialized_views:
                self.log('Refreshing view: {}'.format(view_id))
                # This is quite slow! up to 10 mins.
                cursor.execute("REFRESH MATERIALIZED VIEW %s" % view_id)

    def log(self, message):
        if self.IS_VERBOSE:
            logger.warn(message)
        else:
            logger.info(message)
