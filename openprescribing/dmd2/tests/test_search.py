from django.test import TestCase

from dmd2.models import AMP, AMPP, VMP, VMPP
from dmd2.search import search


class TestSearch(TestCase):
    fixtures = ['dmd-search-fixtures']

    def test_by_snomed_code(self):
        self.assertSearchResults(
            {'q': '318412000'},
            {VMP: [318412000]}
        )

    def test_by_term(self):
        self.assertSearchResults(
            {'q': 'sanofi'},
            {AMP: [632811000001105], AMPP: [1389011000001108]}
        )

    def test_with_obj_types(self):
        self.assertSearchResults(
            {'q': 'acebutolol', 'obj_types': ['vmp']},
            {VMP: [318412000]}
        )

    def test_include_invalid(self):
        # In our test data, all invalid AMPs are also unavailable and have no
        # BNF code, so we need to include those objects here.
        self.assertSearchResults(
            {
                'q': 'phoenix',
                'obj_types': ['amp'],
                'include': ['unavailable', 'no_bnf_code', 'invalid'],
            },
            {AMP: [17747811000001100]}
        )
        self.assertSearchResults(
            {
                'q': 'phoenix',
                'obj_types': ['amp'],
                'include': ['unavailable', 'no_bnf_code'],
            },
            {}
        )

    def test_include_unavailable(self):
        self.assertSearchResults(
            {
                'q': 'kent',
                'obj_types': ['amp'],
                'include': ['unavailable'],
            },
            {AMP: [4814811000001108]}
        )
        self.assertSearchResults(
            {
                'q': 'kent',
                'obj_types': ['amp'],
                'include': [],
            },
            {}
        )

    def test_include_no_bnf_codes(self):
        # In our test data, all AMPs without a BNF code are also unavailable
        # and invalid, so we need to include those objects here.
        self.assertSearchResults(
            {
                'q': 'phoenix',
                'obj_types': ['amp'],
                'include': ['unavailable', 'invalid', 'no_bnf_code'],
            },
            {AMP: [17747811000001100]}
        )
        self.assertSearchResults(
            {
                'q': 'phoenix',
                'obj_types': ['amp'],
                'include': ['unavailable', 'invalid'],
            },
            {}
        )

    def assertSearchResults(self, search_params, exp_result_ids):
        kwargs = {
            'q': '',
            'obj_types': ['vmp', 'vmpp', 'amp', 'ampp'],
            'include': [],
        }
        kwargs.update(search_params)
        results = search(**kwargs)
        result_ids = {
            result['cls']: [obj.pk for obj in result['objs']]
            for result in results
        }

        self.assertEqual(result_ids, exp_result_ids)
