import sqlite3

import numpy
import scipy.sparse

from django.test import SimpleTestCase

from matrixstore.serializer import serialize, serialize_compressed, deserialize


class TestSerializer(SimpleTestCase):

    def test_simple_serialisation(self):
        obj = {'hello': 123}
        self.assertEqual(deserialize(serialize(obj)), obj)

    def test_simple_serialisation_with_compression(self):
        obj = {'hello': 'world' * 256}
        data = serialize(obj)
        compressed_data = serialize_compressed(obj)
        self.assertLess(len(compressed_data), len(data))
        self.assertEqual(deserialize(compressed_data), obj)

    def test_matrix_serialisation(self):
        obj = scipy.sparse.csc_matrix((5, 4))
        new_obj = deserialize(serialize(obj))
        self.assertTrue(numpy.array_equal(obj.todense(), new_obj.todense()))

    def test_dtype_is_preserved(self):
        obj = scipy.sparse.csc_matrix((5, 4), dtype=numpy.uint16)
        new_obj = deserialize(serialize(obj))
        self.assertEqual(obj.dtype, new_obj.dtype)

    def test_sqlite_roundtrip(self):
        obj = {'hello': 123}
        data = serialize(obj)
        new_data = roundtrip_through_sqlite(sqlite3.Binary(data))
        new_obj = deserialize(new_data)
        self.assertEqual(new_obj, obj)

    def test_sqlite_roundtrip_with_compression(self):
        obj = {'hello': 'world' * 256}
        data = serialize_compressed(obj)
        new_data = roundtrip_through_sqlite(sqlite3.Binary(data))
        new_obj = deserialize(new_data)
        self.assertEqual(new_obj, obj)


def roundtrip_through_sqlite(value):
    db = sqlite3.connect(':memory:')
    db.execute('CREATE TABLE data (value BLOB)')
    db.execute('INSERT INTO data VALUES (?)', [value])
    result = db.execute('SELECT value FROM data')
    new_value = result.fetchone()[0]
    db.close()
    return new_value
