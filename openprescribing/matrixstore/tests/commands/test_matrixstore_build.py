"""
This runs a full end-to-end test of the MatrixStore build process using both
BigQuery and Google Cloud Storage.

As this process can take a few minutes to run it can be convenient while
debugging a failing test to keep the resulting SQLite file around and re-use it
between test runs. This can be acheived by setting the environment variable
`PERSIST_MATRIXSTORE_TEST_FILE` to the path where the file should be created
and kept.
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
from django.core.management import call_command
from django.test import SimpleTestCase, override_settings

from matrixstore.serializer import deserialize
from matrixstore.tests.data_factory import DataFactory


@override_settings(PIPELINE_DATA_BASEDIR=None)
class TestMatrixStoreBuild(SimpleTestCase):

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
        cls.tempdir = tempfile.mkdtemp()
        settings.PIPELINE_DATA_BASEDIR = cls.tempdir
        # Optional path at which to preserve test file between runs (see module
        # docstring)
        cls.data_file = os.environ.get('PERSIST_MATRIXSTORE_TEST_FILE')
        if not cls.data_file:
            cls.data_file = os.path.join(cls.tempdir, 'matrixstore_test.sqlite')
        # Upload data to BigQuery and build file
        if not os.path.exists(cls.data_file):
            factory.upload_to_bigquery()
            end_date = max(cls.months_to_import)[:7]
            call_command(
                'matrixstore_build',
                end_date,
                cls.data_file,
                months=len(cls.months_to_import)
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
        for entry in self.practice_statistics:
            practice = entry['practice']
            month = entry['month']
            if month not in self.months_to_import:
                continue
            expected_total_list_size = entry['total_list_size']
            expected_statins_cost = json.loads(entry['star_pu'])['statins_cost']
            total_list_size = get_value('total_list_size', practice, month)
            statins_cost = get_value('star_pu.statins_cost', practice, month)
            self.assertEqual(total_list_size, expected_total_list_size)
            self.assertEqual(statins_cost, expected_statins_cost)

    def test_prescribing_values_are_correct(self):
        for field in ('items', 'quantity', 'net_cost', 'actual_cost'):
            get_value = MatrixValueFetcher(
                self.connection, 'presentation', 'bnf_code', field
            )
            for entry in self._expected_prescribing_values():
                value = get_value(entry['bnf_code'], entry['practice'], entry['month'])
                self.assertEqual(value, entry[field])

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


class MatrixValueFetcher(object):
    """
    Provides convenient access to values stored in matrices in SQLite
    """

    def __init__(self, connection, table, key_field, value_field):
        results = connection.execute(
            'SELECT {}, {} FROM {}'.format(key_field, value_field, table)
        )
        self.matrices = {}
        for key, value in results:
            self.matrices[key] = deserialize(value)
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
