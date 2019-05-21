from itertools import product
import random

from django.test import SimpleTestCase

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

    def test_all_groups(self):
        """
        Tests every combination of group and matrix
        """
        test_cases = product(self.get_groups(), self.get_matrices())
        for (group_name, group_definition), (matrix_name, matrix) in test_cases:
            # Use `subTest` when we upgrade to Python 3
            # with self.subTest(matrix=matrix_name, group=group_name):
            row_grouper = RowGrouper(group_definition)
            grouped_matrix = row_grouper.sum(matrix)
            grouped_matrix = to_list_of_lists(grouped_matrix)
            # Transform the grouped matrix into a dict mapping group IDs to
            # lists of column values
            values = {
                group_id: grouped_matrix[offset]
                for (group_id, offset) in row_grouper.offsets.items()
            }
            # Calculate the same dict the boring way using pure Python
            expected_values = self.get_expected_values(group_definition, matrix)
            # We need to round floats to account for differences between
            # numpy and Python float rounding
            self.assertEqual(
                round_floats(values), round_floats(expected_values)
            )

    def get_expected_values(self, group, matrix):
        expected_values = {}
        for row, group_id in group:
            if group_id not in expected_values:
                expected_values[group_id] = [0.0] * self.columns
            for col in range(self.columns):
                value = matrix[row, col]
                expected_values[group_id][col] += value
        return expected_values

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

    def get_groups(self):
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
