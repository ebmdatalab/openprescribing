import random

import numpy
from scipy.sparse import spmatrix as SparseMatrixBase

from django.test import SimpleTestCase

from matrixstore.matrix_ops import (
    convert_to_smallest_int_type, finalise_matrix, sparse_matrix
)


class TestConvertToSmallestIntType(SimpleTestCase):

    def setUp(self):
        self.random = random.Random()
        self.random.seed(90)

    def test_convert_to_smallest_int(self):
        int_types = sorted(
            [
                numpy.int8,
                numpy.int16,
                numpy.int32,
                numpy.int64,
                numpy.uint8,
                numpy.uint16,
                numpy.uint32,
                numpy.uint64,
            ],
            key=lambda t: numpy.iinfo(t).max
        )
        previous_max = 0
        for numpy_type in int_types:
            iinfo = numpy.iinfo(numpy_type)
            matrix = self._random_matrix(iinfo.min, iinfo.max, previous_max)
            matrix_as_list = matrix.tolist()
            converted = convert_to_smallest_int_type(matrix)
            self.assertEqual(converted.dtype, numpy_type)
            self.assertEqual(converted.tolist(), matrix_as_list)
            previous_max = iinfo.max

    def _random_matrix(self, minimum, maximum, floor):
        """
        Return an integer matrix with random values between `minimum` and
        `maximum` with at least one being larger than `floor` and at least one
        being negative if `minimum` is negative
        """
        value = self.random.randint(floor + 1, maximum)
        if minimum < 0:
            small_value = self.random.randint(minimum, -1)
        else:
            small_value = 0
        # Ensure that the dtype is big enough to hold the maximum value (int_
        # will do for all cases apart from uint64)
        dtype = numpy.promote_types(numpy.int_, numpy.min_scalar_type(maximum))
        matrix = numpy.zeros((2, 2), dtype=dtype)
        matrix[0, 0] = value
        matrix[0, 1] = small_value
        return matrix


class TestFinaliseMatrix(SimpleTestCase):

    def setUp(self):
        self.random = random.Random()
        self.random.seed(14)

    def test_sufficiently_sparse_matrices_remain_sparse(self):
        matrix = sparse_matrix((4, 4))
        for coords in self._random_coords(matrix.shape, sample_density=0.3):
            matrix[coords] = self.random.random()
        finalised = finalise_matrix(matrix)
        self.assertIsInstance(finalised, SparseMatrixBase)

    def test_sufficiently_dense_matrices_are_converted_to_ndarrays(self):
        matrix = sparse_matrix((4, 4))
        for coords in self._random_coords(matrix.shape, sample_density=0.8):
            matrix[coords] = self.random.random()
        finalised = finalise_matrix(matrix)
        self.assertIsInstance(finalised, numpy.ndarray)

    def test_integer_matrices_are_converted_to_smallest_type(self):
        matrix = sparse_matrix((4, 4), integer=True)
        for coords in self._random_coords(matrix.shape, sample_density=0.4):
            matrix[coords] = self.random.randint(1, 127)
        finalised = finalise_matrix(matrix)
        self.assertEqual(finalised.dtype, numpy.uint8)

    def _random_coords(self, shape, sample_density):
        rows, cols = shape
        size = rows * cols
        samples = max(1, int(size * sample_density))
        for n in self.random.sample(xrange(size), samples):
            i = int(n / cols)
            j = n % cols
            yield i, j
