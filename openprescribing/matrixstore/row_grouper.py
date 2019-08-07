from collections import defaultdict

import numpy
import scipy.sparse


class RowGrouper(object):
    """
    The `RowGrouper` class provides a method which sums together groups of
    matrix rows. We generally use it for aggregating practice level data into
    organisations that consist of groups of practices like CCGs or STPs.

    Example usage:

    >>> group_definition = [(0, 'even'), (1, 'odd'), (2, 'even'), (3, 'odd')]
    >>> rows = [
    ...   [1, 2, 3, 4],
    ...   [2, 3, 4, 5],
    ...   [3, 4, 5, 6],
    ...   [4, 5, 6, 7],
    ... ]
    >>> matrix = numpy.array(rows)
    >>> row_grouper = RowGrouper(group_definition)
    >>> row_grouper.sum(matrix)
    array([[ 4,  6,  8, 10],
           [ 6,  8, 10, 12]])
    """

    # Maps group IDs (which are usually strings but can be any hashable and
    # sortable type) to their row offset within the grouped matrix
    offsets = None
    # Maps row offsets in the grouped matrix to the group ID of that row
    ids = None

    def __init__(self, group_assignments):
        """
        `group_assignments` is an iterable of (row_offset, group_id) pairs
        assigning rows to groups

        It's acceptable for a row to appear in multiple groups or not to appear
        in any group at all
        """
        groups = defaultdict(list)
        for row_offset, group_id in group_assignments:
            groups[group_id].append(row_offset)
        # Maps group offset to ID (sorted for consistency)
        self.ids = sorted(groups.keys())
        # Maps group ID to offset
        self.offsets = {
            group_id: group_offset for (group_offset, group_id) in enumerate(self.ids)
        }
        self._group_selectors = [numpy.array(groups[group_id]) for group_id in self.ids]
        # Where each group contains only one row (which is the case whenever
        # we're working with practice level data) there's a much faster path we
        # can take where we just pull out the relevant rows using a single
        # selector. (We need the `groups` check to ensure there is at least one
        # group as this selector can't handle the empty case.)
        if groups and all(len(group) == 1 for group in self._group_selectors):
            self._single_row_groups_selector = numpy.array(
                [rows[0] for rows in self._group_selectors]
            )
        else:
            self._single_row_groups_selector = None

    def sum(self, matrix):
        """
        Sum rows of matrix column-wise, according to their group

        Returns a matrix of shape:

            (number_of_groups X columns_in_original_matrix)
        """
        # Fast path for the "each group contains only one row" case
        if self._single_row_groups_selector is not None:
            return matrix[self._single_row_groups_selector]
        # Initialise an array to contain the output
        rows = len(self._group_selectors)
        columns = matrix.shape[1]
        grouped_output = numpy.empty((rows, columns), dtype=matrix.dtype)
        # This is awkward. We always want to return an `ndarray` even if the
        # input type is `matrix`. But where the input is a `matrix` the `out`
        # argument to `numpy.sum` below must be a `matrix` also. So we need a
        # view on our output array which matches the type of the input array,
        # while leaving the actual `grouped_output` return value always of type
        # `ndarray`.  See the `is_matrix` docstring for more detail.
        if is_matrix(matrix):
            output_view = numpy.asmatrix(grouped_output)
        else:
            output_view = grouped_output
        for group_offset, rows_selector in enumerate(self._group_selectors):
            # Get the rows to be summed
            row_group = matrix[rows_selector]
            # Sum them and write the result into the output array
            numpy.sum(row_group, axis=0, out=output_view[group_offset])
        return grouped_output

    def sum_one_group(self, matrix, group_id):
        """
        Sum the rows of matrix (column-wise) which belong to the specified
        group

        Returns a 1-dimensional array of size: columns_in_original_matrix
        """
        row_selector = self._group_selectors[self.offsets[group_id]]
        row_group = matrix[row_selector]
        group_sum = numpy.sum(row_group, axis=0)
        # See `is_matrix` docstring for more detail here
        if is_matrix(group_sum):
            return group_sum.A[0]
        else:
            return group_sum


def is_matrix(value):
    """
    Return whether `value` is a numpy ndarray or a numpy matrix

    Numpy has two classes for representing two-dimensional arrays: `matrix` and
    `ndarray`. They are very similar but not equivalent, and the docs now
    recommend only using `ndarray` as it's more powerful and more general than
    `matrix`. However, the only sparse representions available are of `matrix`
    type rather than `ndarray` so we're forced to still deal with the `matrix`
    type. (Though it's possible that in future there'll be a sparse `ndarray`:
    https://github.com/scipy/scipy/issues/8162)

    Our strategy is to ensure that whenever we move from a sparse to a dense
    representation we end up with an `ndarray` rather than a `matrix`.
    Fortunately, it's possible to convert between the types without having to
    modify the underlying data, so one can simultaneousy have a `matrix` and
    `ndarray` view on the same set of data in memory.
    """
    # This is harder than it ought to be because `numpy.matrix` inherits from
    # `numpy.ndarray`, but the scipy sparse type doesn't inherit from either
    return isinstance(value, (numpy.matrix, scipy.sparse.compressed._cs_matrix))
