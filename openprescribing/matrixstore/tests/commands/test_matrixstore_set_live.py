import os
import shutil
import tempfile

from django.conf import settings
from django.core.management import call_command
from django.test import SimpleTestCase, override_settings


@override_settings(MATRIXSTORE_BUILD_DIR=None, MATRIXSTORE_LIVE_FILE=None)
class TestMatrixStoreSetLive(SimpleTestCase):

    @classmethod
    def setUpClass(cls):
        cls.devnull = open(os.devnull, 'w')
        cls.tempdir = tempfile.mkdtemp()
        settings.MATRIXSTORE_BUILD_DIR = cls.tempdir
        cls.live_file = os.path.join(cls.tempdir, 'matrixstore_live.sqlite')
        settings.MATRIXSTORE_LIVE_FILE = cls.live_file
        cls.files = {
            'latest_jun': 'matrixstore_2018-06_2018-04-18--18-59_063873dd6fd.sqlite',
            'oldest_jun': 'matrixstore_2018-06_2018-04-15--12-45_d7f468ce31b.sqlite',
            'latest_jan': 'matrixstore_2018-01_2018-03-18--18-59_063873dd6fd.sqlite',
            'oldest_jan': 'matrixstore_2018-01_2018-03-15--12-45_d7f468ce31b.sqlite',
        }
        for name in cls.files.values():
            path = os.path.join(cls.tempdir, name)
            open(path, 'w').close()

    def test_updates_to_latest_with_no_args(self):
        self.call_command()
        self.assertEqual(os.readlink(self.live_file), self.files['latest_jun'])

    def test_updates_to_latest_for_specified_date(self):
        self.call_command(date='2018-01')
        self.assertEqual(os.readlink(self.live_file), self.files['latest_jan'])

    def test_also_accepts_underscore_seperated_dates(self):
        self.call_command(date='2018_01')
        self.assertEqual(os.readlink(self.live_file), self.files['latest_jan'])

    def test_accepts_specific_filename(self):
        self.call_command(filename=self.files['oldest_jun'])
        self.assertEqual(os.readlink(self.live_file), self.files['oldest_jun'])

    def test_throws_error_for_no_matching_date(self):
        with self.assertRaises(RuntimeError):
            self.call_command(date='2010-01')

    def test_throws_error_for_missing_file(self):
        with self.assertRaises(RuntimeError):
            self.call_command(filename='no_such_file')

    def call_command(self, **kwargs):
        call_command('matrixstore_set_live', stdout=self.devnull, **kwargs)

    @classmethod
    def tearDownClass(cls):
        cls.devnull.close()
        shutil.rmtree(cls.tempdir)
