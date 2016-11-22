import csv
import glob
import os
import tempfile

import psycopg2
from django.core.management.base import BaseCommand
from django.db import connection

from common import utils
from ebmdatalab import bigquery


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument('--db_name')
        parser.add_argument('--db_user')
        parser.add_argument('--db_pass')

    def handle(self, *args, **options):
        self.IS_VERBOSE = False
        if options['verbosity'] > 1:
            self.IS_VERBOSE = True
        self.dataset = options.get('dataset', 'hscic')
        self.create_views()

    def create_views(self):
        fpath = os.path.dirname(__file__)
        views = glob.glob(os.path.join(fpath, "./views_sql/*.sql"))
        for view in views:
            f = tempfile.TemporaryFile(mode='r+')
            writer = fieldnames = None
            tablename = "vw__%s" % os.path.basename(view).replace('.sql', '')
            print "Recreating %s:" % tablename
            # Yuck: we do a string replacement here as we don't know
            # how many times a dataset placeholder will appear in
            # advance. And we can't use new-style formatting as some
            # of the SQL has braces in.
            sql = open(view, "r").read().replace('%s', self.dataset)
            print "Running bigquery query..."
            bigquery.query_and_return('ebmdatalab', self.dataset, tablename, sql)
            # send the query to bigquery, download the result
            print "Writing CSV from bigquery to disk..."
            count = 0
            for row in bigquery.get_rows(
                    'ebmdatalab', self.dataset, tablename):
                if writer is None:
                    # Snarf the fieldnames from the first row of data
                    fieldnames = row.keys()
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writerow(row)
                count += 1
            print "Wrote %s rows" % count
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
            print "-------------"
