import pickle
import struct

import lz4.frame

# The magic intial bytes which tell us that a given binary chunk is LZ4
# compressed data
LZ4_MAGIC_NUMBER = struct.pack("<I", 0x184D2204)


def serialize(obj):
    """
    Serialize an arbitrary Python object while exploiting the zero-copy features of
    Pickle Protocol 5 (https://peps.python.org/pep-0574/)

    Pickle does almost all the hard work here but we still need to handle the buffer
    objects. The protocol is designed on the assumption that there exists some
    out-of-band mechanism for passing the buffers around and we want to do this by
    bundling them up into the bytestream. Of course, this means we lose the zero-copy
    property while serializing but we can still do zero-copy deserialization and that's
    the operation which is performance critical for us.

    Benchmarking this on SciPy sparse arrays of the size we deal with gives the
    following (all times in microseconds):

                          deserialize  serialize
        zero-copy pickle  11           806
                 pyarrow  58           8063
            naive pickle  807          4217
    """
    buffers = []
    pickled = pickle.dumps(
        obj,
        protocol=5,
        buffer_callback=lambda buffer: buffers.append(buffer.raw()),
    )
    buffers.append(pickled)
    return serialize_buffers(buffers)


def deserialize_uncompressed(data):
    """
    Inverse of `serialize`

    Note that the resulting object may contain zero-copy views on to the original data.
    """
    buffers = deserialize_buffers(data)
    return pickle.loads(buffers[-1], buffers=buffers)


def serialize_compressed(obj):
    """
    Serialize an arbitrary Python object and compress the result using LZ4
    """
    data = serialize(obj)
    # See commit comments for details of how this compression level was chosen
    return lz4.frame.compress(data, compression_level=10, return_bytearray=True)


def deserialize(data):
    """
    Deserialize binary data, whether compressed or uncompressed
    """
    if data.startswith(LZ4_MAGIC_NUMBER):
        data = lz4.frame.decompress(data, return_bytearray=True)
    return deserialize_uncompressed(data)


def serialize_buffers(buffers):
    """
    Serialize a list of binary data objects to bytes

    Data objects can be of any type that has a length and can be joined
    with bytes (buffer, bytes, bytearray etc).

    Each data object must be less than 2**32 bytes in length and there must be fewer
    than 2**32 of them.
    """
    sizes = [len(buffer) for buffer in buffers]
    header = serialize_ints(sizes)
    return b"".join([header, *buffers])


def deserialize_buffers(data):
    """
    Inverse of `serialize_buffers`

    Returned buffers are zero-copy views on to the original data.
    """
    data = memoryview(data)
    sizes, offset = deserialize_ints(data)
    output = []
    for size in sizes:
        next_offset = offset + size
        output.append(data[offset:next_offset])
        offset = next_offset
    return output


def serialize_ints(ints):
    """
    Serialize a list of positive integers to bytes

    Each int must be less than 2**32 and there must be fewer than 2**32 of them
    (`struct` will enforce this).
    """
    count = len(ints)
    return struct.pack(f"<{count + 1}I", count, *ints)


def deserialize_ints(data):
    """
    Inverse of `serialize_ints`
    """
    count = struct.unpack("<I", data[:4])[0]
    end = 4 + (count * 4)
    return struct.unpack(f"<{count}I", data[4:end]), end
