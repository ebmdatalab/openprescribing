import struct

import pyarrow
from scipy.sparse import csc_matrix
import zstandard


# The magic intial bytes which tell us that a given binary chunk is ZStandard
# compressed data
ZSTD_MAGIC_NUMBER = struct.pack('<I', 0xFD2FB528)


compressor = zstandard.ZstdCompressor(level=16)
decompressor = zstandard.ZstdDecompressor()

context = pyarrow.SerializationContext()


def serialize_csc(matrix):
    """
    Decompose a matrix in Compressed Sparse Column format into more basic data
    types (tuples and numpy arrays) which PyArrow knows how to serialize
    """
    return ((matrix.data, matrix.indices, matrix.indptr), matrix.shape)


def deserialize_csc(args):
    """
    Reconstruct a Compressed Sparse Column matrix from its decomposed parts
    """
    # We construct a `csc_matrix` instance by directly assigning its members,
    # rather than using `__init__` which runs additional checks that
    # significantly slow down deserialization. Because we know these values
    # came from properly constructed matrices we can skip these checks
    (data, indices, indptr), shape = args
    matrix = csc_matrix.__new__(csc_matrix)
    matrix.data = data
    matrix.indices = indices
    matrix.indptr = indptr
    matrix._shape = shape
    return matrix


# Register a custom PyArrow serialization context which knows how to handle
# Compressed Sparse Column (csc) matrices
context.register_type(
    csc_matrix,
    'csc',
    custom_serializer=serialize_csc,
    custom_deserializer=deserialize_csc
)


def serialize(obj):
    """
    Serialize an arbitrary Python object using our custom PyArrow context
    """
    return context.serialize(obj).to_buffer().to_pybytes()


def serialize_compressed(obj):
    """
    Serialize an arbitrary Python object using our custom PyArrow context and
    compress the result using ZStandard
    """
    data = context.serialize(obj).to_buffer()
    return compressor.compress(data)


def deserialize(data):
    """
    Deserialize binary data using our custom PyArrow context, automatically
    detecting compressed data and decompressing if necessary
    """
    if memoryview(data)[:4] == ZSTD_MAGIC_NUMBER:
        data = decompressor.decompress(data)
    return context.deserialize(data)
