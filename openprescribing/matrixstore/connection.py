import os.path
import sqlite3
import urllib.parse

from .serializer import deserialize
from .sql_functions import MatrixSum


class MatrixStore(object):
    def __init__(self, sqlite_connection, filename=":memory:"):
        self.connection = sqlite_connection
        # `cache_key` attributes are used to identify the state of an object for
        # caching purposes. Because we create MatrixStore files with unique
        # names, and because they are immutable once created, we can simply use
        # their names for this purpose. Of course this falls apart for
        # in-memory databases, but since we only ever use these in testing with
        # caching disabled we can live with this.
        self.cache_key = filename.encode("utf8")
        # For easier debugging of custom SQL functions written in Python
        sqlite3.enable_callback_tracebacks(True)
        # LIKE queries must be case-sensitive in order to use an index
        self.connection.execute("PRAGMA case_sensitive_like=ON")
        self.date_offsets = dict(
            self.connection.execute("SELECT date, offset FROM date")
        )
        self.practice_offsets = dict(
            self.connection.execute("SELECT code, offset FROM practice")
        )
        self.dates = sorted_keys(self.date_offsets)
        self.practices = sorted_keys(self.practice_offsets)
        self.connection.create_aggregate("MATRIX_SUM", 1, MatrixSum)

    @classmethod
    def from_file(cls, path):
        if not os.path.exists(path):
            raise RuntimeError("No SQLite file at: " + path)
        encoded_path = urllib.parse.quote(os.path.abspath(path))
        connection = sqlite3.connect(
            "file://{}?immutable=1&mode=ro".format(encoded_path),
            uri=True,
            check_same_thread=False,
        )
        # Enable mmapped I/O by making sure the max mmap size (0 by default)
        # exceeds the file size by a comfortable margin. See:
        # https://www.sqlite.org/mmap.html
        size = os.path.getsize(path)
        # We can't use parameter substitution in PRAGMA statements so we use
        # `format` and force to an integer
        connection.execute("PRAGMA mmap_size={:d}".format(size + 1024 * 1024))
        # Record the name of the current file, first resolving any symlinks.
        # These files are generated with unique names which we can use as part
        # of a cache key
        filename = os.path.basename(os.path.realpath(path))
        return cls(connection, filename=filename)

    def query(self, sql, params=()):
        for row in self.connection.cursor().execute(sql, params):
            yield convert_row_types(row)

    def query_one(self, sql, params=()):
        return next(self.query(sql, params=params))

    def close(self):
        self.connection.close()


def sorted_keys(dictionary):
    sorted_items = sorted(dictionary.items(), key=lambda item: item[1])
    return [key for (key, value) in sorted_items]


def convert_row_types(row):
    return list(map(convert_value, row))


def convert_value(value):
    if isinstance(value, (bytes, memoryview)):
        return deserialize(value)
    else:
        return value
