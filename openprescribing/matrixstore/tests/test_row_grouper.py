from itertools import product
import random

from django.test import SimpleTestCase

import numpy

from matrixstore.matrix_ops import finalise_matrix, sparse_matrix
from matrixstore.row_grouper import RowGrouper


class TestGrouper(SimpleTestCase):

    # Show large diffs on assertEqual failures
    maxDiff = None

    def __init__(self, *args, **kwargs):
        super(TestGrouper, self).__init__(*args, **kwargs)
        self.random = random.Random()
        self.random.seed(507)
        self.rows = 16
        self.columns = 16
        self.shape = (self.rows, self.columns)

    def test_basic_sum_by_group(self):
        """
        Test grouping and summing on a matrix which is small enough to verify
        the results by hand
        """
        group_definition = [(0, 'even'), (1, 'odd'), (2, 'even'), (3, 'odd')]
        rows = [
          [1, 2, 3, 4],
          [2, 3, 4, 5],
          [3, 4, 5, 6],
          [4, 5, 6, 7],
        ]
        matrix = numpy.array(rows)
        row_grouper = RowGrouper(group_definition)
        grouped_matrix = row_grouper.sum(matrix)
        value = to_list_of_lists(grouped_matrix)
        expected_value = [
            [4, 6, 8, 10],
            [6, 8, 10, 12],
        ]
        self.assertEqual(value, expected_value)
        self.assertEqual(row_grouper.ids, ['even', 'odd'])
        self.assertEqual(row_grouper.offsets, {'even': 0, 'odd': 1})

    def test_empty_group_produces_empty_matrix(self):
        """
        Test the empty group edge case
        """
        group_definition = []
        rows = [
          [1, 2, 3, 4],
          [2, 3, 4, 5],
          [3, 4, 5, 6],
          [4, 5, 6, 7],
        ]
        matrix = numpy.array(rows)
        row_grouper = RowGrouper(group_definition)
        grouped_matrix = row_grouper.sum(matrix)
        value = to_list_of_lists(grouped_matrix)
        self.assertEqual(value, [])

    def test_all_group_and_matrix_type_combinations(self):
        """
        Tests every combination of group type and matrix type
        """
        test_cases = product(self.get_group_definitions(), self.get_matrices())
        for (group_name, group_definition), (matrix_name, matrix) in test_cases:
            # Use `subTest` when we upgrade to Python 3
            # with self.subTest(matrix=matrix_name, group=group_name):
            row_grouper = RowGrouper(group_definition)
            grouped_matrix = row_grouper.sum(matrix)
            values = to_list_of_lists(grouped_matrix)
            # Calculate the same dict the boring way using pure Python
            expected_values = self.sum_rows_by_group(group_definition, matrix)
            # We need to round floats to account for differences between
            # numpy and Python float rounding
            self.assertEqual(
                round_floats(values), round_floats(expected_values)
            )

    def sum_rows_by_group(self, group_definition, matrix):
        """
        Given a group definition and a matrix, calculate the column-wise totals
        for each group (just like `row_grouper.sum` would do)
        """
        group_totals = {}
        for row_offset, group_id in group_definition:
            # Initialise a new zero-valued row for this group, if we don't have
            # one already
            if group_id not in group_totals:
                group_totals[group_id] = [0.0] * self.columns
            for column_offset in range(self.columns):
                value = matrix[row_offset, column_offset]
                group_totals[group_id][column_offset] += value
        # Return the group totals as a list of lists, sorted by group_id
        return [
            row for (group_id, row) in sorted(group_totals.items())
        ]

    def get_matrices(self):
        for sparse, integer in product([True, False], repeat=2):
            name = '{structure}.{type}'.format(
                structure='sparse' if sparse else 'dense',
                type='integer' if integer else 'float'
            )
            yield name, self.make_matrix(sparse, integer)

    def make_matrix(self, sparse, integer):
        matrix = sparse_matrix(self.shape, integer=integer)
        sample_density = 0.4 if sparse else 1
        for coords in self._random_coords(self.shape, sample_density):
            value = self.random.randrange(1024) if integer else random.random()
            matrix[coords] = value
        matrix = finalise_matrix(matrix)
        return matrix

    def _random_coords(self, shape, sample_density):
        rows, cols = shape
        size = rows * cols
        samples = max(1, int(size * sample_density))
        for n in self.random.sample(xrange(size), samples):
            i = int(n / cols)
            j = n % cols
            yield i, j

    def get_group_definitions(self):
        return [
            (
                'basic_partition',
                [(row, 'odd' if row % 2 else 'even') for row in range(self.rows)]
            ),
            (
                'one_group_with_all_rows',
                [(row, 'everything') for row in range(self.rows)]
            ),
            (
                'some_rows_not_in_any_groups',
                [(row, 'odd' if row % 2 else 'even') for row in range(self.rows // 2)]
            ),
            (
                'some_rows_in_multiple_groups',
                [(row, 'small') for row in range(self.rows // 2)]
                + [(row, 'odd' if row % 2 else 'even') for row in range(self.rows)]
            ),
            (
                'each_row_in_exactly_one_group',
                [(row, 'row_%s' % row) for row in range(self.rows)]
            ),
            (
                'some_rows_in_exactly_one_group',
                [(row, 'row_%s' % row) for row in range(self.rows) if row % 2]
            ),
        ]


def to_list_of_lists(matrix):
    """
    Convert a 2D matrix into a list of lists
    """
    return [
        [matrix[i, j] for j in range(matrix.shape[1])]
        for i in range(matrix.shape[0])
    ]


def round_floats(value):
    """
    Round all floating point values found anywhere within the supplied data
    structure, recursing our way through any nested lists, tuples or dicts
    """
    if isinstance(value, float):
        return round(value, 9)
    elif isinstance(value, list):
        return [round_floats(i) for i in value]
    elif isinstance(value, tuple):
        return tuple(round_floats(i) for i in value)
    elif isinstance(value, dict):
        return {k: round_floats(v) for (k, v) in value.items()}
    else:
        return value
