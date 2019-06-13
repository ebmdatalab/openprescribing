from django.test import SimpleTestCase
from django.test import TestCase


class GetEnvSettingTests(SimpleTestCase):
    def test_falsey_default(self):
        from common.utils import get_env_setting
        self.assertEqual(get_env_setting('FROB123', ''), '')


class TitleCaseTests(SimpleTestCase):
    def test_variaous_cases(self):
        from common.utils import nhs_titlecase
        tests = [
            (
                'THING BY THE CHURCH',
                'Thing by the Church'
            ),
            (
                'DR AS RAGHUNATH AND PTNRS',
                'Dr AS Raghunath and Ptnrs'
            ),
            (
                'OUT OF HOURS',
                'Out of Hours'
            ),
            (
                'NHS CORBY CCG',
                'NHS Corby CCG'
            ),
            (
                'CN HIV THREE BOROUGHS TEAM',
                'CN HIV Three Boroughs Team'
            ),
            (
                'DMC VICARAGE LANE',
                'DMC Vicarage Lane'
            ),
            (
                'DR CHEUNG KK PRACTICE',
                'Dr Cheung KK Practice'
            ),
            (
                'DR PM OPIE & DR AE SPALDING PRACTICE',
                'Dr PM Opie & Dr AE Spalding Practice'
            ),
            (
                'LUNDWOOD MEDICAL CENTRE PMS PRACTICE',
                'Lundwood Medical Centre PMS Practice'
            ),
            (
                "ST ANN'S MEDICAL CENTRE",
                "St Ann's Medical Centre"
            ),
            (
                "C&RH BIGGIN HILL",
                "C&RH Biggin Hill")
        ]
        for words, expected in tests:
            self.assertEquals(nhs_titlecase(words), expected)


def _cluster_count(cursor):
    cursor.execute("""
        SELECT
          count(*)
        FROM
          pg_index AS idx
        JOIN
          pg_class AS i
        ON
          i.oid = idx.indexrelid
        WHERE
          idx.indisclustered
          AND idx.indrelid::regclass = 'tofu'::regclass;
    """)
    return cursor.fetchone()[0]


class FunctionalTests(TestCase):
    fixtures = ['orgs']

    def test_reconstructor_does_work(self):
        from django.db import connection
        from common.utils import constraint_and_index_reconstructor

        with connection.cursor() as cursor:
            # Set up a table
            cursor.execute("CREATE TABLE firmness (id integer PRIMARY KEY)")
            cursor.execute("""
                CREATE TABLE tofu (
                  id integer PRIMARY KEY,
                  brand varchar,
                  firmness_id integer REFERENCES firmness (id))
            """)
            cursor.execute("CLUSTER tofu USING tofu_pkey")
            cursor.execute("CREATE INDEX ON tofu (brand)")
            with constraint_and_index_reconstructor('tofu'):
                cursor.execute(
                    "SELECT count(*) FROM pg_indexes WHERE tablename = 'tofu'"
                )
                self.assertEqual(cursor.fetchone()[0], 0)
            cursor.execute(
                "SELECT count(*) FROM pg_indexes WHERE tablename = 'tofu'"
            )
            self.assertEqual(cursor.fetchone()[0], 2)
            self.assertEqual(_cluster_count(cursor), 1)
