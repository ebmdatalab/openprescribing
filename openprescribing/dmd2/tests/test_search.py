from django.db.models import Q
from django.test import TestCase

from dmd2.build_search_query import build_query_obj
from dmd2.build_rules import build_rules
from dmd2.models import AMP, AMPP, VMP
from dmd2.search import search


class TestSearch(TestCase):
    fixtures = ["dmd-objs"]

    def test_by_snomed_code(self):
        self.assertSearchResults({"q": "318412000"}, {VMP: [318412000]})

    def test_by_term(self):
        self.assertSearchResults(
            {"q": "sanofi"}, {AMP: [632811000001105], AMPP: [1389011000001108]}
        )

    def test_by_bnf_code(self):
        self.assertSearchResults(
            {"q": "0204000C0BB"}, {AMP: [632811000001105], AMPP: [1389011000001108]}
        )

    def test_with_obj_types(self):
        self.assertSearchResults(
            {"q": "acebutolol", "obj_types": ["vmp"]}, {VMP: [318412000]}
        )

    def test_with_no_obj_types(self):
        self.assertSearchResults(
            {"q": "sanofi", "obj_types": []},
            {AMP: [632811000001105], AMPP: [1389011000001108]},
        )

    def test_include_invalid(self):
        # In our test data, all invalid AMPs are also unavailable and have no
        # BNF code, so we need to include those objects here.
        self.assertSearchResults(
            {
                "q": "phoenix",
                "obj_types": ["amp"],
                "include": ["unavailable", "no_bnf_code", "invalid"],
            },
            {AMP: [17747811000001100]},
        )
        self.assertSearchResults(
            {
                "q": "phoenix",
                "obj_types": ["amp"],
                "include": ["unavailable", "no_bnf_code"],
            },
            {},
        )

    def test_include_unavailable(self):
        self.assertSearchResults(
            {"q": "kent", "obj_types": ["amp"], "include": ["unavailable"]},
            {AMP: [4814811000001108]},
        )
        self.assertSearchResults({"q": "kent", "obj_types": ["amp"], "include": []}, {})

    def test_include_no_bnf_codes(self):
        # In our test data, all AMPs without a BNF code are also unavailable
        # and invalid, so we need to include those objects here.
        self.assertSearchResults(
            {
                "q": "phoenix",
                "obj_types": ["amp"],
                "include": ["unavailable", "invalid", "no_bnf_code"],
            },
            {AMP: [17747811000001100]},
        )
        self.assertSearchResults(
            {
                "q": "phoenix",
                "obj_types": ["amp"],
                "include": ["unavailable", "invalid"],
            },
            {},
        )

    def assertSearchResults(self, search_params, exp_result_ids):
        kwargs = {"q": "", "obj_types": ["vmp", "vmpp", "amp", "ampp"], "include": []}
        kwargs.update(search_params)
        results = search(**kwargs)
        result_ids = {
            result["cls"]: [obj.pk for obj in result["objs"]] for result in results
        }

        self.assertEqual(result_ids, exp_result_ids)


class TestAdvancedSearchHelpers(TestCase):
    search = [
        "or",
        [
            ["and", [["nm", "contains", "sugar"], ["sug_f", "equal", False]]],
            ["and", [["nm", "contains", "gluten"], ["glu_f", "equal", False]]],
        ],
    ]

    def test_build_query_obj(self):
        q1 = Q(nm__icontains="sugar") & Q(sug_f=False)
        q2 = Q(nm__icontains="gluten") & Q(glu_f=False)
        expected_query_obj = q1 | q2

        self.assertTreesEqual(build_query_obj(VMP, self.search), expected_query_obj)

    def test_build_rules(self):
        expected_rules = {
            "condition": "OR",
            "rules": [
                {
                    "condition": "AND",
                    "rules": [
                        {"id": "nm", "operator": "contains", "value": "sugar"},
                        {"id": "sug_f", "operator": "equal", "value": 0},
                    ],
                },
                {
                    "condition": "AND",
                    "rules": [
                        {"id": "nm", "operator": "contains", "value": "gluten"},
                        {"id": "glu_f", "operator": "equal", "value": 0},
                    ],
                },
            ],
        }

        self.assertEqual(build_rules(self.search), expected_rules)

    def assertTreesEqual(self, t1, t2):
        # Once we upgrade to 2.0, we can drop this as Q.__eq__ will be defined.
        if not isinstance(t1, Q):
            self.assertEqual(t1, t2)
            return

        self.assertEqual(t1.__class__, t2.__class__)
        self.assertEqual(t1.connector, t2.connector)
        self.assertEqual(t1.negated, t2.negated)
        self.assertEqual(len(t1.children), len(t2.children))

        for c1, c2 in zip(t1.children, t2.children):
            self.assertTreesEqual(c1, c2)
