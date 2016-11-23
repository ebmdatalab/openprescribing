import csv
import glob
import logging
import os
import tempfile

from django.core.management.base import BaseCommand
from django.db import connection

from common import utils
from ebmdatalab import bigquery

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """A command to create 'views' (actually ordinary tables) in postgres
    for subsets of data commonly requested over the API.

    Materialized views are too slow to build, so instead we generate
    the data in BigQuery and then load it into existing tables.

    The tables are not managed by Django so do not have models. They
    were created using the SQL at
    frontend/management/commands/replace_matviews.sql (also used by the tests).

    """
    def handle(self, *args, **options):
        self.IS_VERBOSE = False
        if options['verbosity'] > 1:
            self.IS_VERBOSE = True
        self.dataset = options.get('dataset', 'hscic')
        self.fill_views()

    def fill_views(self):
        fpath = os.path.dirname(__file__)
        views = glob.glob(os.path.join(fpath, "./views_sql/*.sql"))
        for view in views:
            f = tempfile.TemporaryFile(mode='r+')
            writer = fieldnames = None
            tablename = "vw__%s" % os.path.basename(view).replace('.sql', '')
            self.log("Recreating %s:" % tablename)
            # We do a string replacement here as we don't know how
            # many times a dataset substitution token (i.e. `%s`) will
            # appear in each SQL template. And we can't use new-style
            # formatting as some of the SQL has braces in.
            sql = open(view, "r").read().replace('%s', self.dataset)
            self.log("Running bigquery query...")
            bigquery.query_and_return(
                'ebmdatalab', self.dataset, tablename, sql)
            self.log("Writing CSV from bigquery to disk...")
            count = 0
            for row in bigquery.get_rows(
                    'ebmdatalab', self.dataset, tablename):
                if writer is None:
                    # Snarf the fieldnames from the first row of data
                    fieldnames = row.keys()
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writerow(row)
                count += 1
            self.log("Wrote %s rows" % count)
            if count > 0:
                copy_str = "COPY %s(%s) FROM STDIN "
                copy_str += "WITH (FORMAT CSV)"
                f.seek(0)
                with connection.cursor() as cursor:
                    with utils.constraint_and_index_reconstructor(tablename):
                        print "Deleting from table..."
                        cursor.execute("DELETE FROM %s" % tablename)
                        print "Copying CSV to postgres..."
                        print len(f.read().split("\n"))
                        f.seek(0)
                        cursor.copy_expert(copy_str % (
                            tablename, ','.join(fieldnames)), f)
            f.close()
            self.log("-------------")

    def log(self, message):
        if self.IS_VERBOSE:
            logger.warn(message)
        else:
            logger.info(message)
