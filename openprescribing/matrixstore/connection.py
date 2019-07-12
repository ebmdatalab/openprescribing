import os.path
import sqlite3

from .serializer import deserialize
from .sql_functions import MatrixSum


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
        # Enable mmapped I/O by making sure the max mmap size (0 by default)
        # exceeds the file size by a comfortable margin. See:
        # https://www.sqlite.org/mmap.html
        size = os.path.getsize(path)
        # We can't use parameter substitution in PRAGMA statements so we use
        # `format` and force to an integer
        connection.execute('PRAGMA mmap_size={:d}'.format(size + 1024*1024))
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
