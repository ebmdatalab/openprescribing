import sqlite3

from matrixstore.connection import MatrixStore
from matrixstore.tests.import_test_data_fast import import_test_data_fast


def matrixstore_from_data_factory(data_factory):
    """
    Returns a new in-memory MatrixStore instance using the data from the
    supplied DataFactory
    """
    connection = sqlite3.connect(':memory:')
    end_date = max(data_factory.months)[:7]
    months = len(data_factory.months)
    import_test_data_fast(connection, data_factory, end_date, months=months)
    return MatrixStore(connection)
