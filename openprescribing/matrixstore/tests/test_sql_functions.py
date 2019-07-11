from django.test import SimpleTestCase

import numpy
import scipy.sparse

from matrixstore.sql_functions import fast_in_place_add


class TestFastInPlaceAdd(SimpleTestCase):

    def test_fast_in_place_add(self):
        matrix_a = [
            [1, 0, 2],
            [0, 0, 0],
            [0, 4, 5],
            [2, 3, 2],
        ]
        matrix_b = [
            [0, 0, 0],
            [0, 0, 4],
            [1, 1, 1],
            [3, 2, 0],
        ]
        sparse_matrix_a = scipy.sparse.csc_matrix(numpy.array(matrix_a))
        sparse_matrix_b = scipy.sparse.csc_matrix(numpy.array(matrix_b))
        accumulator = numpy.zeros((4, 3), order='F')
        fast_in_place_add(accumulator, sparse_matrix_a)
        fast_in_place_add(accumulator, sparse_matrix_b)
        self.assertEqual(
            accumulator.tolist(),
            [
                [1, 0, 2],
                [0, 0, 4],
                [1, 5, 6],
                [5, 5, 2],
            ]
        )
