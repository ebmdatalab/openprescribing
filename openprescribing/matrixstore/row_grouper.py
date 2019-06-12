from collections import defaultdict

import numpy


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
            group_id: group_offset
            for (group_offset, group_id) in enumerate(self.ids)
        }
        self._group_selectors = [
            numpy.array(groups[group_id])
            for group_id in self.ids
        ]
        # Where each group contains only one row (which is the case whenever
        # we're working with practice level data) there's a much faster path we
        # can take where we just pull out the relevant rows using a single
        # selector
        if all(len(group) == 1 for group in self._group_selectors):
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
        rows = len(self._group_selectors)
        columns = matrix.shape[1]
        grouped = numpy.empty((rows, columns), dtype=matrix.dtype)
        for group_offset, rows_selector in enumerate(self._group_selectors):
            row_group = matrix[rows_selector]
            grouped[group_offset] = numpy.sum(row_group, axis=0)
        return grouped
