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

        self.conn = psycopg2.connect(database=db_name, user=db_user,
                                     password=db_pass)
        cursor = self.conn.cursor()

        self.create_indexes(cursor)
        self.analyze_db(cursor)

        self.conn.commit()
        self.conn.close()

    def create_indexes(self, cursor):
        if self.IS_VERBOSE:
            print 'Adding indexes...'
        # Used for presentation-by-practice queries.
        cmd = 'CREATE INDEX frontend_prescription_by_practice_and_date ON '
        cmd += 'frontend_prescription(presentation_code varchar_pattern_ops, '
        cmd += 'processing_date, actual_cost, total_items)'
        self._print_and_execute(cursor, cmd)
        cmd = 'CREATE INDEX frontend_prescription_by_practice ON '
        cmd += 'frontend_prescription(presentation_code varchar_pattern_ops, '
        cmd += 'practice_id, actual_cost, total_items)'
        self._print_and_execute(cursor, cmd)

    def analyze_db(self, cursor):
        if self.IS_VERBOSE:
            print 'Analyzing database...'
        self._print_and_execute(cursor, 'ANALYZE VERBOSE')

    def _print_and_execute(self, cursor, cmd):
        if self.IS_VERBOSE:
            print cmd
        cursor.execute(cmd)
        self.conn.commit()
