"""
This tests the MatrixStore build process:

    `TestMatrixStoreBuild` runs entirely in memory and therefore shortcuts
    various parts of the build process which involve downloading data from
    BigQuery

    'TestMatrixStoreBuildEndToEnd` runs the same set of tests but uploads data
    to BigQuery and exports it to Google Cloud Storage in order to excercise
    the full build process

As this end-to-end test can take a few minutes to run it can be convenient
while debugging a failing test to keep the resulting SQLite file around and
re-use it between test runs. This can be acheived by setting the environment
variable `PERSIST_MATRIXSTORE_TEST_FILE` to the path where the file should be
created and kept.
"""
from __future__ import print_function

from collections import defaultdict
import os
import json
import numbers
import shutil
import sqlite3
import tempfile
import warnings

from django.conf import settings
from django.test import SimpleTestCase, override_settings

import numpy

from matrixstore.serializer import deserialize
from matrixstore.tests.data_factory import DataFactory
from matrixstore.tests.import_test_data_fast import import_test_data_fast
from matrixstore.tests.import_test_data_full import import_test_data_full


class TestMatrixStoreBuild(SimpleTestCase):
    """
    Runs a test of the MatrixStore build process entirely in memory
    """

    @classmethod
    def setUpClass(cls):
        factory = DataFactory()
        cls.months = factory.create_months('2019-01-01', 3)
        cls.closed_practice = factory.create_practice()
        cls.active_practices = factory.create_practices(3)
        cls.practice_statistics = factory.create_practice_statistics(
            cls.active_practices, cls.months
        )
        factory.create_practice_statistics(
            [cls.closed_practice], cls.months
        )
        cls.presentations = factory.create_presentations(4)
        cls.prescribing = factory.create_prescribing(
            cls.presentations, cls.active_practices, cls.months
        )
        # Create a presentation which changes its BNF code and create some
        # prescribing with both old and new codes
        cls.presentation_to_update = factory.create_presentation()
        cls.updated_presentation = factory.update_bnf_code(cls.presentation_to_update)
        cls.prescribing_with_old_code = factory.create_prescribing(
            [cls.presentation_to_update], cls.active_practices, cls.months
        )
        cls.prescribing_with_new_code = factory.create_prescribing(
            [cls.updated_presentation], cls.active_practices, cls.months
        )
        # We deliberately import data for fewer months than we've created so we
        # can test that only the right data is included
        cls.months_to_import = cls.months[1:]
        # The closed practice only prescribes in the month we don't import, so
        # it shouldn't show up at all in our data
        factory.create_prescription(
            cls.presentations[0], cls.closed_practice, cls.months[0]
        )
        # The format of `end_date` only uses year and month
        end_date = max(cls.months_to_import)[:7]
        months = len(cls.months_to_import)
        cls.create_matrixstore(factory, end_date, months)

    @classmethod
    def create_matrixstore(cls, data_factory, end_date, months):
        cls.connection = sqlite3.connect(':memory:')
        import_test_data_fast(
            cls.connection,
            data_factory,
            end_date,
            months=months
        )

    @classmethod
    def tearDownClass(cls):
        cls.connection.close()

    def setUp(self):
        # Reset this as at least one test modifies it
        self.connection.row_factory = None

    def test_dates_are_correct(self):
        dates = [
            row[0] for row in
            self.connection.execute('SELECT date FROM date ORDER BY offset')
        ]
        expected_dates = [date[:10] for date in self.months_to_import]
        self.assertEqual(dates, expected_dates)

    def test_practices_are_correct(self):
        practice_codes = [
            row[0] for row in
            self.connection.execute('SELECT code FROM practice ORDER BY code')
        ]
        expected_codes = sorted(
            [practice['code'] for practice in self.active_practices]
        )
        self.assertEqual(practice_codes, expected_codes)
        self.assertNotIn(self.closed_practice['code'], practice_codes)

    def test_presentations_are_correct(self):
        expected = list(self.presentations)
        expected.append(self.updated_presentation)
        expected.sort(key=lambda i: i['bnf_code'])
        # Allow us to get results as dicts
        self.connection.row_factory = sqlite3.Row
        results = self.connection.execute(
            """
            SELECT
              bnf_code, is_generic, adq_per_quantity, name
            FROM
              presentation
            ORDER BY
              bnf_code
            """
        )
        results = [dict(row) for row in results]
        self.assertEqual(results, expected)
        self.assertNotIn(self.presentation_to_update, results)

    def test_practice_statistics_are_correct(self):
        get_value = MatrixValueFetcher(
            self.connection, 'practice_statistic', 'name', 'value'
        )
        expected_entries = 0
        for entry in self.practice_statistics:
            practice = entry['practice']
            month = entry['month']
            if month not in self.months_to_import:
                continue
            for field, expected_value in entry.items():
                if field in ('month', 'practice', 'pct_id', 'star_pu'):
                    continue
                expected_entries += 1
                value = get_value(field, practice, month)
                self.assertEqual(value, expected_value)
            for name, expected_value in json.loads(entry['star_pu']).items():
                expected_entries += 1
                value = get_value('star_pu.' + name, practice, month)
                self.assertEqual(value, expected_value)
        # Check there are no additional values that we weren't expecting
        self.assertEqual(get_value.nonzero_values, expected_entries)

    def test_prescribing_values_are_correct(self):
        for field in ['items', 'quantity', 'net_cost', 'actual_cost']:
            # Cost figures are originally in pounds but we store them in pence
            # as ints
            multiplier = 100 if field.endswith('_cost') else 1
            get_value = MatrixValueFetcher(
                self.connection, 'presentation', 'bnf_code', field
            )
            expected_entries = 0
            for entry in self._expected_prescribing_values():
                expected_entries += 1
                value = get_value(entry['bnf_code'], entry['practice'], entry['month'])
                expected_value = round(entry[field] * multiplier)
                self.assertEqual(value, expected_value)
            # Check there are no additional values that we weren't expecting
            self.assertEqual(get_value.nonzero_values, expected_entries)

    def _expected_prescribing_values(self):
        # First we yield the standard prescribing, filtered by month
        for entry in self.prescribing:
            if entry['month'] in self.months_to_import:
                yield entry
        # Next we sum together prescribing done under both our old and new BNF
        # code and yield the results under the new BNF code
        summed_values = defaultdict(dict)
        for entry in self.prescribing_with_old_code + self.prescribing_with_new_code:
            current_value = summed_values[entry['practice'], entry['month']]
            sum_dicts(current_value, entry)
        for (practice, month), values in summed_values.items():
            if month in self.months_to_import:
                yield {
                    'bnf_code': self.updated_presentation['bnf_code'],
                    'practice': practice,
                    'month': month,
                    'items': values['items'],
                    'quantity': values['quantity'],
                    'net_cost': values['net_cost'],
                    'actual_cost': values['actual_cost'],
                }


@override_settings(PIPELINE_DATA_BASEDIR=None)
class TestMatrixStoreBuildEndToEnd(TestMatrixStoreBuild):
    """
    Runs the same test as above but as a full integration test against actual
    BigQuery and Google Cloud Storage
    """

    @classmethod
    def create_matrixstore(cls, data_factory, end_date, months):
        cls.tempdir = tempfile.mkdtemp()
        settings.PIPELINE_DATA_BASEDIR = cls.tempdir
        # Optional path at which to preserve test file between runs (see module
        # docstring)
        cls.data_file = os.environ.get('PERSIST_MATRIXSTORE_TEST_FILE')
        if not cls.data_file:
            cls.data_file = os.path.join(cls.tempdir, 'matrixstore_test.sqlite')
        # Upload data to BigQuery and build file
        if not os.path.exists(cls.data_file):
            import_test_data_full(
                cls.data_file,
                data_factory,
                end_date,
                months=months
            )
        else:
            warnings.warn(
                'Skipping test of matrixstore_build and re-using file at: {}'.format(
                    cls.data_file
                )
            )

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tempdir)

    def setUp(self):
        # We have to check this because the `sqlite3.connect` call will
        # implicitly create the file if it doesn't exist
        if not os.path.exists(self.data_file):
            raise RuntimeError('No SQLite file created')
        self.connection = sqlite3.connect(self.data_file)

    def tearDown(self):
        self.connection.close()


class MatrixValueFetcher(object):
    """
    Provides convenient access to values stored in matrices in SQLite
    """

    def __init__(self, connection, table, key_field, value_field):
        results = connection.execute(
            'SELECT {}, {} FROM {}'.format(key_field, value_field, table)
        )
        self.matrices = {}
        self.nonzero_values = 0
        for key, value in results:
            matrix = deserialize(value)
            self.matrices[key] = matrix
            self.nonzero_values += numpy.count_nonzero(matrix)
        self.practices = dict(connection.execute('SELECT code, offset FROM practice'))
        self.dates = dict(connection.execute('SELECT date, offset FROM date'))
        for date, offset in list(self.dates.items()):
            self.dates[date + ' 00:00:00 UTC'] = offset

    def __call__(self, key, practice, date):
        """
        Find the row in `table` where `key_field` matches `key` and extract the
        matrix stored in `value_field`. Return the value at the row and column
        corresponding to `practice` and `date`
        """
        row = self.practices[practice]
        column = self.dates[date]
        return self.matrices[key][row, column]


def sum_dicts(current_values, new_values):
    """
    Add the numeric parts of `new_values` to `current_values`
    """
    for field, value in new_values.items():
        if not isinstance(value, numbers.Number):
            continue
        zero = type(value)()
        current_values[field] = current_values.get(field, zero) + value
