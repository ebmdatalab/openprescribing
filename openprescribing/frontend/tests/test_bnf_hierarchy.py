import random
from itertools import product

from django.test import TestCase
from frontend.utils.bnf_hierarchy import _prune_paths, simplify_bnf_codes
from matrixstore.tests.contextmanagers import (
    patched_global_matrixstore_from_data_factory,
)
from matrixstore.tests.data_factory import DataFactory


class TestPrunePaths(TestCase):
    def test_example(self):
        # Test the example described in the docstring of _prune_paths.

        all_paths = ["AAA", "AAB", "ABA", "ABB", "BAA", "BAB", "BBA", "BBB"]
        paths = ["AAA", "ABA", "ABB", "BAA", "BAB"]
        self.assertEqual(_prune_paths(paths, all_paths), ["AAA", "AB", "BA"])

    def test_full(self):
        # With a set of paths built from a complete binary tree of height 6, choose a
        # subset of paths of each length between 1 and 63, and check that _prune_paths
        # does not raise an AssertionError for that subset.

        random.seed(123)
        all_paths = ["".join(tpl) for tpl in product(*["AB" for _ in range(6)])]

        for size in range(1, 2**6):
            paths = random.sample(all_paths, size)
            _prune_paths(paths, all_paths)


class TestSimplifyBnfCodes(TestCase):
    def test_simplify_bnf_codes(self):
        # These are BNF codes for some of the presentations for two different products,
        # Co-Careldopa (generic, 0409010N0AA) and Sinemet (branded, 0409010N0BB).
        #
        # We check that simplifying a list of BNF codes for the branded presentations
        # returns the BNF prefix of the branded product.

        all_bnf_codes = [
            "0409010N0AAAAAA",
            "0409010N0AAABAB",
            "0409010N0AAACAC",
            "0409010N0AAADAD",
            "0409010N0AAAEAE",
            "0409010N0BBAAAA",
            "0409010N0BBABAC",
            "0409010N0BBACAB",
            "0409010N0BBADAD",
        ]

        factory = DataFactory()
        month = factory.create_months("2018-10-01", 1)[0]
        practice = factory.create_practices(1)[0]
        for bnf_code in all_bnf_codes:
            presentation = factory.create_presentation(bnf_code)
            factory.create_prescription(presentation, practice, month)

        branded_bnf_codes = [
            "0409010N0BBAAAA",
            "0409010N0BBABAC",
            "0409010N0BBACAB",
            "0409010N0BBADAD",
            "0409010N0BBAEAE",  # This is missing from all_bnf_codes.
        ]

        with patched_global_matrixstore_from_data_factory(factory):
            self.assertEqual(simplify_bnf_codes(branded_bnf_codes), ["0409010N0BB"])
