import psycopg2
from django.core.management.base import BaseCommand
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
        db_host = utils.get_env_setting('DB_HOST')
        self.conn = psycopg2.connect(database=db_name, user=db_user,
                                     password=db_pass, host=db_host)
        cursor = self.conn.cursor()

        self.create_foreign_keys(cursor)
        self.analyze_db(cursor)

        self.conn.commit()
        self.conn.close()

    def create_foreign_keys(self, cursor):
        if self.IS_VERBOSE:
            print('Adding foreign key references...')
        prefix = 'ALTER TABLE frontend_prescription '
        prefix += 'ADD CONSTRAINT frontend_prescription'
        suffix = ' ON DELETE CASCADE'
        indexes = [
            {'fk': 'sha_id', 'table': 'frontend_sha', 'pk': 'code'},
            {'fk': 'pct_id', 'table': 'frontend_pct', 'pk': 'code'},
            {'fk': 'chemical_id', 'table': 'frontend_chemical',
             'pk': 'bnf_code'},
            {'fk': 'practice_id', 'table': 'frontend_practice', 'pk': 'code'}
        ]
        for index in indexes:
            cmd = '%s_%s_fkey ' % (prefix, index['fk'])
            cmd += 'FOREIGN KEY (%s) ' % index['fk']
            cmd += 'REFERENCES %s(%s) ' % (index['table'], index['pk'])
            cmd += suffix
            self._print_and_execute(cursor, cmd)

    def analyze_db(self, cursor):
        if self.IS_VERBOSE:
            print('Analyzing database...')
        self._print_and_execute(cursor, 'ANALYZE VERBOSE')

    def _print_and_execute(self, cursor, cmd):
        if self.IS_VERBOSE:
            print(cmd)
        cursor.execute(cmd)
        self.conn.commit()
