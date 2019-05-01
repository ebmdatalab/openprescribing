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

    @classmethod
    def tearDownClass(cls):
        cls.matrixstore.close()
