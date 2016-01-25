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

        self.vacuum_db(cursor)
        self.create_matviews(cursor)
        self.analyze_db(cursor)

        self.conn.commit()
        self.conn.close()

    def create_matviews(self, cursor):
        if self.IS_VERBOSE:
            print 'Adding materialized views...'

        # Spending by presentation_id by CCG by month.
        cmd = 'CREATE MATERIALIZED VIEW vw__presentation_summary_by_ccg AS '
        cmd += 'SELECT processing_date, pct_id, presentation_code, '
        cmd += 'SUM(total_items) AS items, '
        cmd += 'SUM(actual_cost) AS cost, '
        cmd += 'CAST(SUM(quantity) AS bigint) AS quantity '
        cmd += 'FROM frontend_prescription '
        cmd += 'GROUP BY processing_date, pct_id, presentation_code'
        self._print_and_execute(cursor, cmd)

        # Indexes by usage.
        cmd = 'CREATE INDEX vw__idx_pres_by_ccg_pres_code ON '
        cmd += 'vw__presentation_summary_by_ccg'
        cmd += '(presentation_code varchar_pattern_ops)'
        self._print_and_execute(cursor, cmd)

        cmd = 'CREATE INDEX vw__idx_pres_by_ccg_joint_code ON '
        cmd += 'vw__presentation_summary_by_ccg(pct_id, presentation_code)'
        self._print_and_execute(cursor, cmd)

        # Total spending by presentation_id by month.
        cmd = 'CREATE MATERIALIZED VIEW vw__presentation_summary AS '
        cmd += 'SELECT processing_date, presentation_code, '
        cmd += 'SUM(items) AS items, '
        cmd += 'SUM(cost) AS cost, '
        cmd += 'CAST(SUM(quantity) AS bigint) AS quantity '
        cmd += 'FROM vw__presentation_summary_by_ccg '
        cmd += 'GROUP BY processing_date, presentation_code'
        self._print_and_execute(cursor, cmd)

        # Indexes by uage.
        cmd = 'CREATE INDEX vw__idx_presentation_summary ON '
        cmd += 'vw__presentation_summary(presentation_code varchar_pattern_ops)'
        self._print_and_execute(cursor, cmd)

        # CREATE MATERIALIZED VIEW vw_presentation_summary AS
        # SELECT processing_date, presentation_code,
        # SUM(items) AS items, SUM(cost) AS cost
        # FROM vw_presentation_summary_by_ccg
        # GROUP BY processing_date, pct_id, presentation_code;

        # Spending by chemical_id by CCG by month.
        cmd = 'CREATE MATERIALIZED VIEW vw__chemical_summary_by_ccg AS '
        cmd += 'SELECT processing_date, pct_id, chemical_id, '
        cmd += 'SUM(total_items) AS items, '
        cmd += 'SUM(actual_cost) AS cost, '
        cmd += 'CAST(SUM(quantity) AS bigint) AS quantity '
        cmd += 'FROM frontend_prescription '
        cmd += 'GROUP BY processing_date, pct_id, chemical_id'
        self._print_and_execute(cursor, cmd)

        # Indexes by usage.
        cmd = 'CREATE INDEX vw__idx_chem_by_ccg ON '
        cmd += 'vw__chemical_summary_by_ccg(chemical_id varchar_pattern_ops, pct_id)'
        self._print_and_execute(cursor, cmd)

        cmd = 'CREATE INDEX vw__idx_ccg_by_chem ON '
        cmd += 'vw__chemical_summary_by_ccg(pct_id, chemical_id varchar_pattern_ops)'
        self._print_and_execute(cursor, cmd)

        # Spending by chemical_id by practice by month.
        cmd = 'CREATE MATERIALIZED VIEW vw__chemical_summary_by_practice'
        cmd += ' AS '
        cmd += 'SELECT processing_date, practice_id, chemical_id, '
        cmd += 'SUM(total_items) AS items, '
        cmd += 'SUM(actual_cost) AS cost, '
        cmd += 'CAST(SUM(quantity) AS bigint) AS quantity '
        cmd += 'FROM frontend_prescription '
        cmd += 'GROUP BY processing_date, practice_id, chemical_id'
        self._print_and_execute(cursor, cmd)

        # Indexes in order of usage.
        cmd = 'CREATE INDEX vw__idx_practice_by_chem ON '
        cmd += 'vw__chemical_summary_by_practice '
        cmd += '(chemical_id varchar_pattern_ops, practice_id)'
        self._print_and_execute(cursor, cmd)

        cmd = 'CREATE INDEX vw__idx_chem_by_practice ON '
        cmd += 'vw__chemical_summary_by_practice '
        cmd += '(practice_id, chemical_id varchar_pattern_ops)'
        self._print_and_execute(cursor, cmd)

        cmd = 'CREATE INDEX idx_chem_by_practice_bydate ON '
        cmd += 'vw__chemical_summary_by_practice '
        cmd += '(chemical_id varchar_pattern_ops, processing_date)'
        self._print_and_execute(cursor, cmd)

        # Spending by practice by month.
        cmd = 'CREATE MATERIALIZED VIEW vw__practice_summary AS '
        cmd += 'SELECT processing_date, practice_id, '
        cmd += 'SUM(total_items) AS items, '
        cmd += 'SUM(actual_cost) AS cost, '
        cmd += 'CAST(SUM(quantity) AS bigint) AS quantity '
        cmd += 'FROM frontend_prescription '
        cmd += 'GROUP BY processing_date, practice_id'
        self._print_and_execute(cursor, cmd)

        cmd = 'CREATE INDEX vw__practice_summary_prac_id ON '
        cmd += 'vw__practice_summary(practice_id)'
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
        self._print_and_execute(cursor, 'ANALYZE VERBOSE')

    def _print_and_execute(self, cursor, cmd):
        if self.IS_VERBOSE:
            print cmd
        cursor.execute(cmd)
        self.conn.commit()
