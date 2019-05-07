from collections import defaultdict
import numbers

from django.test import SimpleTestCase

from matrixstore.tests.data_factory import DataFactory
from matrixstore.tests.matrixstore_factory import matrixstore_from_data_factory


class TestMatrixStoreConnection(SimpleTestCase):

    @classmethod
    def setUpClass(cls):
        cls.factory = DataFactory()
        cls.factory.create_all(
            start_date='2018-06-01',
            num_months=6,
            num_practices=6,
            num_presentations=6,
        )
        cls.matrixstore = matrixstore_from_data_factory(cls.factory)

    def test_practice_offsets(self):
        practice_codes = sorted(p['code'] for p in self.factory.practices)
        expected_offsets = dict(zip(practice_codes, range(len(practice_codes))))
        self.assertEqual(self.matrixstore.practice_offsets, expected_offsets)

    def test_date_offsets(self):
        dates = sorted(m[:10] for m in self.factory.months)
        expected_offsets = dict(zip(dates, range(len(dates))))
        self.assertEqual(self.matrixstore.date_offsets, expected_offsets)

    def test_query(self):
        excluded_code = self.factory.presentations[0]['bnf_code']
        results = self.matrixstore.query(
            'SELECT bnf_code, items FROM presentation WHERE bnf_code != ?',
            [excluded_code]
        )
        results = list(results)
        for bnf_code, items_matrix in results:
            self.assertNotEqual(bnf_code, excluded_code)
            self.assertIsInstance(items_matrix[0, 0], numbers.Number)
        self.assertGreaterEqual(len(results), 1)

    def test_query_one(self):
        target_code = self.factory.presentations[0]['bnf_code']
        bnf_code, items_matrix = self.matrixstore.query_one(
            'SELECT bnf_code, items FROM presentation WHERE bnf_code = ?',
            [target_code]
        )
        self.assertEqual(bnf_code, target_code)
        self.assertIsInstance(items_matrix[0, 0], numbers.Number)

    def test_matrix_sum(self):
        target_codes = [p['bnf_code'] for p in self.factory.presentations][:3]
        items_matrix = self.matrixstore.query_one(
            'SELECT MATRIX_SUM(items) FROM presentation WHERE bnf_code IN (?, ? ,?)',
            target_codes
        )[0]
        items_dict = defaultdict(int)
        for p in self.factory.prescribing:
            if p['bnf_code'] in target_codes:
                items_dict[p['practice'], p['month'][:10]] += p['items']
        for practice, row_offset in self.matrixstore.practice_offsets.items():
            for date, col_offset in self.matrixstore.date_offsets.items():
                value = items_matrix[row_offset, col_offset]
                expected_value = items_dict[practice, date]
                self.assertEqual(value, expected_value)

    @classmethod
    def tearDownClass(cls):
        cls.matrixstore.close()
