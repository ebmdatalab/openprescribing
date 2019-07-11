import sqlite3

from .matrix_ops import zeros_like
from .serializer import serialize, deserialize


class MatrixSum(object):

    accumulator = None

    def step(self, value):
        if value is None:
            return
        matrix = deserialize(value)
        if self.accumulator is None:
            self.accumulator = zeros_like(matrix)
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
