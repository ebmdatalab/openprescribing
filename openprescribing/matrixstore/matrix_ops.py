import numpy
import scipy.sparse


def sparse_matrix(shape, integer=False):
    """
    Create a new sparse matrix (either integer or floating point) in a form
    suitable for populating with data
    """
    dtype = numpy.int_ if integer else numpy.float_
    return scipy.sparse.lil_matrix(shape, dtype=dtype)


def finalise_matrix(matrix):
    """
    Return a copy of a sparse matrix in a form suitable for storage
    """
    matrix = matrix.tocsc()
    matrix.sort_indices()
    if is_integer(matrix):
        matrix = convert_to_smallest_int_type(matrix)
    matrix = convert_to_dense_if_smaller(matrix)
    return matrix


def zeros_like(matrix, order=None):
    """
    Return a zero-valued matrix of the same shape as `matrix` and with
    equivalent integer or floating point type

    Note this differs from `numpy.zeros_like` in that it always uses the
    largest integer type (int_) even if the source matrix uses a smaller type
    (e.g.  uint8). This is so that we have sufficient headroom to sum many
    matrices together.
    """
    dtype = numpy.int_ if is_integer(matrix) else numpy.float_
    return numpy.zeros(matrix.shape, dtype=dtype, order=order)


def is_integer(matrix):
    """
    Return whether or not the matrix has integer type
    """
    return numpy.issubdtype(matrix.dtype, numpy.integer)


def convert_to_dense_if_smaller(matrix):
    """
    Convert a sparse matrix to a dense one if that would result in less overall
    memory usage

    This isn't primarily about storage space as once compressed there isn't
    much difference between the two forms, but the smaller representations are
    faster to work with when summing.
    """
    if get_dense_memory_usage(matrix) < get_sparse_memory_usage(matrix):
        return matrix.toarray()
    else:
        return matrix


def get_sparse_memory_usage(matrix):
    """
    Return the number of bytes need to store a sparse matrix
    """
    return matrix.data.nbytes + matrix.indices.nbytes + matrix.indptr.nbytes


def get_dense_memory_usage(matrix):
    """
    Return the number of bytes need to store the equivalent dense
    representation of a sparse matrix
    """
    return matrix.dtype.itemsize * matrix.shape[0] * matrix.shape[1]


def convert_to_smallest_int_type(matrix):
    """
    Convert a matrix to use the smallest integer type capable of representing
    all the values currently stored in it
    """
    target_type = smallest_int_type_for_range(matrix.min(), matrix.max())
    if target_type != matrix.dtype:
        matrix = matrix.astype(target_type, copy=False)
    return matrix


def smallest_int_type_for_range(minimum, maximum):
    """
    Return smallest numpy integer type capable of representing all values in
    the supplied range
    """
    signed = minimum < 0
    abs_max = max(maximum, abs(minimum))
    if signed:
        if abs_max < 1 << 7:
            return numpy.int8
        elif abs_max < 1 << 15:
            return numpy.int16
        elif abs_max < 1 << 31:
            return numpy.int32
    else:
        if abs_max < 1 << 8:
            return numpy.uint8
        elif abs_max < 1 << 16:
            return numpy.uint16
        elif abs_max < 1 << 32:
            return numpy.uint32
    # Return default integer type (other than in the exceptional case that the
    # value is too big to store in a signed 64-bit int)
    if not signed and abs_max > 1 << 63:
        return numpy.uint64
    else:
        return numpy.int64
