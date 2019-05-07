import os.path
import sqlite3

from .matrix_ops import zero_like
from .serializer import serialize, deserialize


class MatrixStore(object):

    def __init__(self, sqlite_connection):
        self.connection = sqlite_connection
        # For easier debugging of custom SQL functions written in Python
        sqlite3.enable_callback_tracebacks(True)
        # LIKE queries must be case-sensitive in order to use an index
        self.connection.execute('PRAGMA case_sensitive_like=ON')
        self.date_offsets = dict(
            self.connection.execute('SELECT date, offset FROM date')
        )
        self.practice_offsets = dict(
            self.connection.execute('SELECT code, offset FROM practice')
        )
        self.connection.create_aggregate('MATRIX_SUM', 1, MatrixSum)

    @classmethod
    def from_file(cls, path):
        if not os.path.exists(path):
            raise RuntimeError('No SQLite file at: '+path)
        connection = sqlite3.connect(
            path,
            # Given that we treat the file as read-only we can happily share
            # the connection across threads, should we want to
            check_same_thread=False
        )
        return cls(connection)

    def query(self, sql, params=()):
        for row in self.connection.cursor().execute(sql, params):
            yield convert_row_types(row)

    def query_one(self, sql, params=()):
        return next(self.query(sql, params=params))

    def close(self):
        self.connection.close()


def convert_row_types(row):
    return map(convert_value, row)


def convert_value(value):
    if isinstance(value, (bytes, buffer)):
        return deserialize(value)
    else:
        return value


class MatrixSum(object):

    accumulator = None

    def step(self, value):
        if value is None:
            return
        matrix = deserialize(value)
        if self.accumulator is None:
            self.accumulator = zero_like(matrix)
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
