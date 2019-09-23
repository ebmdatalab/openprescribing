import mock
import sqlite3

from matrixstore.connection import MatrixStore
from matrixstore import db
from matrixstore.tests.import_test_data_fast import import_test_data_fast


def matrixstore_from_data_factory(data_factory, end_date=None, months=None):
    """
    Returns a new in-memory MatrixStore instance using the data from the
    supplied DataFactory
    """
    # We need this connection to be sharable across threads because
    # LiveServerTestCase runs in a separate thread from the main test code
    connection = sqlite3.connect(":memory:", check_same_thread=False)
    end_date = max(data_factory.months)[:7] if end_date is None else end_date
    months = len(data_factory.months) if months is None else months
    import_test_data_fast(connection, data_factory, end_date, months=months)
    return MatrixStore(connection)


def patch_global_matrixstore(matrixstore):
    """
    Temporarily replace the global MatrixStore instance (as accessed via
    `matrixstore.db.get_db`) with the supplied matrixstore

    Returns a function which undoes the monkeypatching
    """
    patcher = mock.patch("matrixstore.connection.MatrixStore.from_file")
    mocked = patcher.start()
    mocked.return_value = matrixstore
    # There are memoized functions so we clear any previously memoized value
    db.get_db.cache_clear()
    db.get_row_grouper.cache_clear()

    def stop_patching():
        patcher.stop()
        db.get_db.cache_clear()
        db.get_row_grouper.cache_clear()
        matrixstore.close()

    return stop_patching
