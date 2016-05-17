import os
import psycopg2
import unittest
from django.core.management import call_command
from django.test import TestCase
from common import utils


def setUpModule():
    fix_dir = 'frontend/tests/fixtures/'
    call_command('loaddata', fix_dir + 'chemicals.json',
                 verbosity=0)
    call_command('loaddata', fix_dir + 'ccgs.json',
                 verbosity=0)
    call_command('loaddata', fix_dir + 'practices.json',
                 verbosity=0)
    call_command('loaddata', fix_dir + 'shas.json',
                 verbosity=0)
    call_command('loaddata', fix_dir + 'prescriptions.json',
                 verbosity=0)
    call_command('loaddata', fix_dir + 'practice_listsizes.json',
                 verbosity=0)
    args = []
    db_name = 'test_' + utils.get_env_setting('DB_NAME')
    db_user = utils.get_env_setting('DB_USER')
    db_pass = utils.get_env_setting('DB_PASS')
    opts = {
        'db_name': db_name,
        'db_user': db_user,
        'db_pass': db_pass
    }
    call_command('create_matviews', *args, **opts)


def tearDownModule():
    args = []
    db_name = 'test_' + utils.get_env_setting('DB_NAME')
    db_user = utils.get_env_setting('DB_USER')
    db_pass = utils.get_env_setting('DB_PASS')
    opts = {
        'db_name': db_name,
        'db_user': db_user,
        'db_pass': db_pass
    }
    call_command('drop_matviews', *args, **opts)
    call_command('flush', verbosity=0, interactive=False)


class CommandsTestCase(TestCase):

    def test_import_create_matviews(self):
        db_name = 'test_' + utils.get_env_setting('DB_NAME')
        db_user = utils.get_env_setting('DB_USER')
        db_pass = utils.get_env_setting('DB_PASS')
        db_host = utils.get_env_setting('DB_HOST')
        self.conn = psycopg2.connect(database=db_name, user=db_user,
                                     password=db_pass, host=db_host)
        with self.conn.cursor() as c:

            cmd = 'SELECT * FROM vw__practice_summary '
            cmd += 'ORDER BY processing_date, practice_id'
            c.execute(cmd)
            results = c.fetchall()
            self.assertEqual(len(results), 10)
            self.assertEqual(results[9][1], 'P87629')
            self.assertEqual(results[9][2], 55)
            self.assertEqual(results[9][3], 64.26)
            self.assertEqual(results[9][4], 2599)

            cmd = 'SELECT * FROM vw__presentation_summary '
            cmd += 'ORDER BY processing_date'
            c.execute(cmd)
            results = c.fetchall()
            self.assertEqual(len(results), 11)
            self.assertEqual(results[9][1], '0204000I0BCAAAB')
            self.assertEqual(results[9][2], 29)
            self.assertEqual(results[9][3], 32.26)
            self.assertEqual(results[9][4], 2350)

            cmd = 'SELECT * FROM vw__presentation_summary_by_ccg '
            cmd += 'ORDER BY processing_date, presentation_code'
            c.execute(cmd)
            results = c.fetchall()
            self.assertEqual(len(results), 12)
            self.assertEqual(results[9][1], '03V')
            self.assertEqual(results[9][2], '0202010B0AAABAB')
            self.assertEqual(results[9][3], 62)
            self.assertEqual(results[9][4], 54.26)
            self.assertEqual(results[9][5], 2788)

            cmd = 'SELECT * FROM vw__chemical_summary_by_ccg '
            cmd += 'ORDER BY processing_date, chemical_id'
            c.execute(cmd)
            results = c.fetchall()
            self.assertEqual(len(results), 11)
            self.assertEqual(results[10][1], '03V')
            self.assertEqual(results[10][2], '0204000I0')
            self.assertEqual(results[10][3], 33)
            self.assertEqual(results[10][4], 36.28)
            self.assertEqual(results[10][5], 2354)

            cmd = 'SELECT * FROM vw__chemical_summary_by_practice '
            cmd += 'ORDER BY processing_date, practice_id'
            c.execute(cmd)
            results = c.fetchall()
            self.assertEqual(len(results), 13)
            self.assertEqual(results[10][1], 'K83059')
            self.assertEqual(results[10][2], '0204000I0')
            self.assertEqual(results[10][3], 16)
            self.assertEqual(results[10][4], 14.15)
            self.assertEqual(results[10][5], 1154)

            cmd = 'SELECT * FROM vw__ccgstatistics '
            cmd += 'ORDER BY date, pct_id'
            c.execute(cmd)
            results = c.fetchall()
            self.assertEqual(len(results), 3)
            self.assertEqual(results[0][1], '03Q')
            self.assertEqual(results[0][2], 'NHS Vale of York')
            self.assertEqual(results[0][3], 25)
            self.assertEqual(results[0][4], 819.2)
            self.assertEqual(results[0][5], 489.7)
            self.assertEqual(results[0][-1]['oral_antibacterials_item'], 10)

        self.conn.close()
