from django.test import SimpleTestCase

import numpy
import scipy.sparse

from matrixstore.sql_functions import fast_in_place_add, MatrixSum


class TestMatrixSum(SimpleTestCase):
    def test_simple_addition(self):
        matrix_a = [[1, 0, 2], [0, 0, 0], [0, 4, 5], [2, 3, 2]]
        matrix_b = [[0, 0, 0], [0, 0, 4], [1, 1, 1], [3, 2, 0]]
        ndarray_a = numpy.array(matrix_a)
        sparse_matrix_b = scipy.sparse.csc_matrix(numpy.array(matrix_b))

        matrix_sum = MatrixSum()
        matrix_sum.add(ndarray_a)
        matrix_sum.add(sparse_matrix_b)
        value = matrix_sum.value()

        self.assertEqual(value.tolist(), [[1, 0, 2], [0, 0, 4], [1, 5, 6], [5, 5, 2]])

    def test_value_error_on_empty_sum(self):
        with self.assertRaises(ValueError):
            matrix_sum = MatrixSum()
            matrix_sum.value()

    def test_fast_in_place_add(self):
        matrix_a = [[1, 0, 2], [0, 0, 0], [0, 4, 5], [2, 3, 2]]
        matrix_b = [[0, 0, 0], [0, 0, 4], [1, 1, 1], [3, 2, 0]]
        sparse_matrix_a = scipy.sparse.csc_matrix(numpy.array(matrix_a))
        sparse_matrix_b = scipy.sparse.csc_matrix(numpy.array(matrix_b))
        accumulator = numpy.zeros((4, 3), order="F")
        fast_in_place_add(accumulator, sparse_matrix_a)
        fast_in_place_add(accumulator, sparse_matrix_b)
        self.assertEqual(
            accumulator.tolist(), [[1, 0, 2], [0, 0, 4], [1, 5, 6], [5, 5, 2]]
        )
