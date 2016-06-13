import csv
import psycopg2
from django.core.management.base import BaseCommand, CommandError
from frontend.models import Section
from common import utils


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument('--db_name')
        parser.add_argument('--db_user')
        parser.add_argument('--db_pass')

    def handle(self, *args, **options):
        self.IS_VERBOSE = False
        if options['verbosity'] > 1:
            self.IS_VERBOSE = True

        if options['db_name']:
            db_name = options['db_name']
        else:
            db_name = utils.get_env_setting('DB_NAME')
        if options['db_user']:
            db_user = options['db_user']
        else:
            db_user = utils.get_env_setting('DB_USER')
        if options['db_pass']:
            db_pass = options['db_pass']
        else:
            db_pass = utils.get_env_setting('DB_PASS')
        db_host = utils.get_env_setting('DB_HOST', '127.0.0.1')
        self.conn = psycopg2.connect(database=db_name, user=db_user,
                                     password=db_pass, host=db_host)
        cursor = self.conn.cursor()

        self.refresh_matviews(cursor)
        self.vacuum_db(cursor)
        self.analyze_db(cursor)

        self.conn.close()

    def refresh_matviews(self, cursor):
        if self.IS_VERBOSE:
            print 'Refreshing materialized views...'
        refresh = 'REFRESH MATERIALIZED VIEW'
        cmd = '%s vw__presentation_summary_by_ccg' % refresh
        self._print_and_execute(cursor, cmd)
        cmd = '%s vw__presentation_summary' % refresh
        self._print_and_execute(cursor, cmd)
        cmd = '%s vw__chemical_summary_by_ccg' % refresh
        self._print_and_execute(cursor, cmd)
        cmd = '%s vw__chemical_summary_by_practice' % refresh
        self._print_and_execute(cursor, cmd)
        cmd = '%s vw__practice_summary' % refresh
        self._print_and_execute(cursor, cmd)
        cmd = '%s vw__ccgstatistics' % refresh
        self._print_and_execute(cursor, cmd)

    def vacuum_db(self, cursor):
        if self.IS_VERBOSE:
            print 'Vacuuming database...'
        old_isolation_level = self.conn.isolation_level
        self.conn.set_isolation_level(0)
        query = "VACUUM"
        self._print_and_execute(cursor, query)
        self.conn.set_isolation_level(old_isolation_level)

    def analyze_db(self, cursor):
        if self.IS_VERBOSE:
            print 'Analyzing database...'
        cursor.execute('ANALYZE VERBOSE')

    def _print_and_execute(self, cursor, cmd):
        if self.IS_VERBOSE:
            print cmd
        cursor.execute(cmd)
        self.conn.commit()
