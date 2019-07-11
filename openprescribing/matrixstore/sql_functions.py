import sqlite3

from scipy.sparse import csc_matrix, _sparsetools

from .matrix_ops import zeros_like
from .serializer import serialize, deserialize


class MatrixSum(object):

    accumulator = None

    def step(self, value):
        if value is None:
            return
        matrix = deserialize(value)
        if self.accumulator is None:
            # We need this to be in Fortran (i.e. column-major) order for the
            # fast addition path below to work
            self.accumulator = zeros_like(matrix, order='F')
        try:
            fast_in_place_add(self.accumulator, matrix)
        except FastInPlaceAddError:
            self.accumulator += matrix

    def finalize(self):
        if self.accumulator is not None:
            # Operations on SciPy sparse matrices sometimes return matrix
            # objects rather than the standard 2-dimensional numpy array. See:
            # https://github.com/scipy/scipy/issues/7510
            # We always want array values (for one thing, pyarrow can't
            # serialize matrix instances out of the box) and so we convert them
            # here by grabbing the underlying array from the matrix object, if
            # that's what we've got. (Note: this is the documented conversion
            # method; we're not using a private API)
            try:
                value = self.accumulator.A
            except AttributeError:
                value = self.accumulator
            return sqlite3.Binary(serialize(value))


class FastInPlaceAddError(Exception):
    pass


def fast_in_place_add(accumulator, matrix):
    """
    Attempt fast in-place addition of `matrix` (a sparse CSC matrix) to
    `accumulator` (an ndarray of the same size)

    Raises FastInPlaceAddError if the operation can't be performed and standard
    addition should be used instead

    This is based on the code found in:
        scipy/sparse/compressed.py:_cs_matrix._add_dense
    """
    if not isinstance(matrix, csc_matrix):
        raise FastInPlaceAddError()
    if accumulator.shape != matrix.shape:
        raise FastInPlaceAddError()
    if not accumulator.flags.f_contiguous:
        raise FastInPlaceAddError()
    # In order to use Compressed Sparse Row (csr) operations with Compressed
    # Sparse Column (csc) matrices we need to transpose the matrix
    # we're adding into. This is a fast operation which just returns a new view
    # on the underlying data.
    transposed = accumulator.transpose()
    rows, columns = transposed.shape
    _sparsetools.csr_todense(
        rows, columns, matrix.indptr, matrix.indices, matrix.data, transposed
    )
