from urllib.parse import parse_qs

from django.db.models import Q
from django.test import TestCase

from matrixstore.tests.contextmanagers import (
    patched_global_matrixstore_from_data_factory,
)
from matrixstore.tests.data_factory import DataFactory

from dmd.build_search_query import build_query_obj
from dmd.build_rules import build_rules
from dmd.models import AMP, AMPP, VMP, VMPP
from dmd.search import advanced_search, search


class TestSearch(TestCase):
    fixtures = ["dmd-objs"]

    def test_by_snomed_code(self):
        self.assertSearchResults({"q": "318412000"}, {VMP: [318412000]})

    def test_by_gtin(self):
        self.assertSearchResults({"q": "5036850012349"}, {AMPP: [1389011000001108]})
        self.assertSearchResults(
            {"q": "5060061161275"}, {AMPP: [19374211000001101, 19374211000001102]}
        )

    def test_by_term(self):
        self.assertSearchResults(
            {"q": "sanofi"}, {AMP: [632811000001105], AMPP: [1389011000001108]}
        )

    def test_by_bnf_code(self):
        self.assertSearchResults(
            {"q": "0204000C0BB"}, {AMP: [632811000001105], AMPP: [1389011000001108]}
        )

    def test_by_integer_bnf_code(self):
        self.assertSearchResults(
            {"q": "0204"},
            {
                VMP: [318412000],
                AMP: [632811000001105],
                VMPP: [1098611000001105],
                AMPP: [1389011000001108],
            },
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


class TestAdvancedSearch(TestCase):
    fixtures = ["dmd-objs"]

    def test_advanced_search(self):
        bnf_codes = [
            "0204000C0AAAAAA",  # Acebut HCl_Cap 100mg
            "0204000C0BBAAAA",  # Sectral_Cap 100mg
            "0204000D0AAAAAA",  # Practolol_Inj 2mg/ml 5ml Amp
        ]

        factory = DataFactory()
        factory.create_prescribing_for_bnf_codes(bnf_codes)

        search = ["nm", "contains", "acebutolol"]

        with patched_global_matrixstore_from_data_factory(factory):
            results = advanced_search(AMP, search, ["unavailable"])

        self.assertFalse(results["too_many_results"])
        self.assertCountEqual(
            results["objs"],
            AMP.objects.filter(pk__in=[10347111000001100, 4814811000001108]),
        )
        querystring = results["analyse_url"].split("#")[1]
        params = parse_qs(querystring)
        self.assertEqual(
            params, {"numIds": ["0204000C0AA"], "denom": ["total_list_size"]}
        )


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

        self.assertEqual(build_query_obj(VMP, self.search), expected_query_obj)

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
