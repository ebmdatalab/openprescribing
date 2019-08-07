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
            self.accumulator = zeros_like(matrix, order="F")
        if isinstance(matrix, csc_matrix):
            fast_in_place_add(self.accumulator, matrix)
        else:
            self.accumulator += matrix

    def finalize(self):
        if self.accumulator is not None:
            return sqlite3.Binary(serialize(self.accumulator))


def fast_in_place_add(ndarray, matrix):
    """
    Performs fast in-place addition of a sparse CSC matrix to an ndarray of the
    same size

    This is based on the code found in:
        scipy/sparse/compressed.py:_cs_matrix._add_dense
    """
    if ndarray.shape != matrix.shape:
        raise ValueError(
            "Shapes do not match: {} vs {}".format(ndarray.shape, matrix.shape)
        )
    if not ndarray.flags.f_contiguous:
        raise ValueError("ndarray must be in Fortran order")
    # In order to use Compressed Sparse Row (csr) operations with Compressed
    # Sparse Column (csc) matrices we need to transpose the matrix
    # we're adding into. This is a fast operation which just returns a new view
    # on the underlying data.
    transposed = ndarray.transpose()
    rows, columns = transposed.shape
    _sparsetools.csr_todense(
        rows, columns, matrix.indptr, matrix.indices, matrix.data, transposed
    )
