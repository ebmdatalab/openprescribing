from __future__ import print_function
import logging

from django.core.management.base import BaseCommand
from django.db import connection

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    "A command to refresh our materialized views in Postgres"

    def handle(self, *args, **options):
        log = logger.warn if options["verbosity"] > 1 else logger.info

        materialized_views = ["vw__medians_for_tariff"]

        with connection.cursor() as cursor:
            for view_id in materialized_views:
                log("Refreshing view: {}".format(view_id))
                # This is quite slow! up to 10 mins.
                cursor.execute("REFRESH MATERIALIZED VIEW %s" % view_id)
