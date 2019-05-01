import datetime
import os
import shutil
import sqlite3
import tempfile
import time

from django.test import SimpleTestCase

from matrixstore.build.init_db import (
    SCHEMA_SQL, generate_dates, import_dates
)
from matrixstore.build.generate_filename import generate_filename


class TestGenerateFilename(SimpleTestCase):

    @classmethod
    def setUpClass(cls):
        cls.tempdir = tempfile.mkdtemp()

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tempdir)

    def test_generate_filename(self):
        filename = os.path.join(self.tempdir, 'test.sqlite')
        connection = sqlite3.connect(filename)
        connection.executescript(SCHEMA_SQL)
        import_dates(connection, generate_dates('2018-10-01'))
        connection.commit()
        connection.close()
        last_modified = time.mktime(
            datetime.datetime(2018, 12, 6, 15, 5, 3).timetuple()
        )
        os.utime(filename, (last_modified, last_modified))
        new_filename = generate_filename(filename)
        self.assertRegexpMatches(
            new_filename,
            'matrixstore_2018-10_2018-12-06--15-05_[a-f0-9]{16}\.sqlite'
        )
