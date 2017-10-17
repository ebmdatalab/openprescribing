from django.test import TestCase
from django.db import OperationalError


class ApiTestUtils(TestCase):
    def test_db_timeout(self):
        from api.view_utils import db_timeout

        @db_timeout(1)
        def do_long_running_query():
            from django.db import connection
            cursor = connection.cursor()
            cursor.execute("select pg_sleep(0.01);")

        self.assertRaises(OperationalError, do_long_running_query)
