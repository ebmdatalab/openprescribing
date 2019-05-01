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
