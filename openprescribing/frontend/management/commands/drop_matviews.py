import psycopg2
from django.core.management.base import BaseCommand, CommandError
from common import utils

'''
Used for testing.
'''


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument('--db_name')
        parser.add_argument('--db_user')
        parser.add_argument('--db_pass')

    def handle(self, *args, **options):
        db_name = options['db_name']
        db_user = options['db_user']
        db_pass = options['db_pass']
        db_host = utils.get_env_setting('DB_HOST')
        self.conn = psycopg2.connect(database=db_name, user=db_user,
                                     password=db_pass, host=db_host)
        with self.conn.cursor() as c:
            cmd = 'DROP MATERIALIZED VIEW vw__presentation_summary; '
            cmd += 'DROP MATERIALIZED VIEW vw__presentation_summary_by_ccg; '
            cmd += 'DROP MATERIALIZED VIEW vw__chemical_summary_by_ccg; '
            cmd += 'DROP MATERIALIZED VIEW vw__chemical_summary_by_practice; '
            cmd += 'DROP MATERIALIZED VIEW vw__practice_summary; '
            cmd += 'DROP MATERIALIZED VIEW vw__ccgstatistics; '
            c.execute(cmd)
        self.conn.commit()
        self.conn.close()
