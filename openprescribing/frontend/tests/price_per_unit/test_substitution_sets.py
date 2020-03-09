from django.test import TestCase

from frontend.price_per_unit.substitution_sets import (
    get_substitution_sets_from_bnf_codes,
    groups_from_pairs,
)

PRESENTATIONS = {
    "generic_metformin": "0601022B0AAASAS",
    "branded_metformin": "0601022B0BJADAS",
    "generic_inhaler": "0302000C0AABFBF",
    "gsk_inhaler": "0302000C0BCAEBF",
    "branded_tramadol_tablet": "040702040BTAAAC",
    "branded_tramadol_capsule": "040702040BJABAH",
    "finetest_test_strips": "0601060D0EDAAA0",
    "element_test_strips": "0601060D0DBAAA0",
}


class SubstitutionSetsTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        bnf_codes = PRESENTATIONS.values()
        cls.substitution_sets = get_substitution_sets_from_bnf_codes(
            bnf_codes, "frontend/tests/fixtures/price_per_unit/formulation_swaps.csv"
        )
        # Make an inverse mapping of presentations to the set which contains
        # them
        cls.presentation_to_set = {}
        for substitution_set in cls.substitution_sets.values():
            for presentation in substitution_set.presentations:
                cls.presentation_to_set[presentation] = substitution_set.id

    def assertSubstitutable(self, presentation_a, presentation_b, invert=False):
        bnf_code_a = PRESENTATIONS[presentation_a]
        bnf_code_b = PRESENTATIONS[presentation_b]
        # Using `object()` as the default makes all missing values compare
        # non-equal
        substitution_set_a = self.presentation_to_set.get(bnf_code_a, object())
        substitution_set_b = self.presentation_to_set.get(bnf_code_b, object())
        if not invert:
            self.assertEqual(substitution_set_a, substitution_set_b)
        else:
            self.assertNotEqual(substitution_set_a, substitution_set_b)

    def assertNotSubstitutable(self, presentation_a, presentation_b):
        self.assertSubstitutable(presentation_a, presentation_b, invert=True)

    def test_substituting_generic_for_brand(self):
        self.assertSubstitutable("generic_metformin", "branded_metformin")

    def test_excluded_presentations_ignored(self):
        self.assertNotSubstitutable("generic_inhaler", "gsk_inhaler")

    def test_substituting_branded_capsule_for_branded_tablet(self):
        self.assertSubstitutable("branded_tramadol_tablet", "branded_tramadol_capsule")

    def test_substituting_glucose_test_strips(self):
        self.assertSubstitutable("finetest_test_strips", "element_test_strips")


class GroupsFromPairsTest(TestCase):
    def test_groups_from_pairs(self):
        # fmt: off
        pairs = [
            (1, 2),
            (3, 4),
            (5, 6),
            (1, 3),
        ]
        expected_groups = [
            [1, 2, 3, 4],
            [5, 6]
        ]
        # fmt: on
        self.assertEqual(list(groups_from_pairs(pairs)), expected_groups)
