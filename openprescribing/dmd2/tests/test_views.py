from django.test import TestCase

from dmd2.models import DtPaymentCategory
from frontend.models import Presentation, TariffPrice
from frontend.tests.data_factory import DataFactory


class TestDMDObjView(TestCase):
    fixtures = ['dmd-objs']

    def test_vtm(self):
        rsp = self.client.get('/dmd/vtm/68088000/')
        self.assertContains(rsp, '<td>Name</td><td>Acebutolol</td>', html=True)
        self.assertNotContains(rsp, 'This VTM cannot be matched')

    def test_vmp(self):
        rsp = self.client.get('/dmd/vmp/318412000/')
        self.assertContains(
            rsp,
            '<td>Name</td><td>Acebutolol 100mg capsules</td>',
            html=True
        )
        self.assertNotContains(rsp, 'Analyse prescribing')
        self.assertNotContains(rsp, 'See prices paid')

        factory = DataFactory()
        practice = factory.create_practice()
        presentation = Presentation.objects.create(
            bnf_code='0204000C0AAAAAA',
            name='Acebut HCl_Cap 100mg'
        )
        factory.create_prescribing_for_practice(practice, [presentation])

        rsp = self.client.get('/dmd/vmp/318412000/')
        self.assertContains(rsp, 'Analyse prescribing')
        self.assertContains(rsp, 'See prices paid')

    def test_amp(self):
        rsp = self.client.get('/dmd/amp/632811000001105/')
        self.assertContains(
            rsp,
            '<td>Description</td><td>Sectral 100mg capsules (Sanofi)</td>',
            html=True
        )

    def test_vmpp(self):
        rsp = self.client.get('/dmd/vmpp/1098611000001105/')
        self.assertContains(
            rsp,
            '<td>Description</td><td>Acebutolol 100mg capsules 84 capsule</td>',
            html=True
        )
        self.assertNotContains(rsp, 'View Drug Tariff history')

        TariffPrice.objects.create(
            date='2019-07-01',
            vmpp_id=1098611000001105,
            tariff_category=DtPaymentCategory.objects.create(cd=1, descr='Cat A'),
            price_pence=100,
        )

        rsp = self.client.get('/dmd/vmpp/1098611000001105/')
        self.assertContains(rsp, 'View Drug Tariff history')

    def test_ampp(self):
        rsp = self.client.get('/dmd/ampp/9703311000001100/')
        self.assertContains(
            rsp,
            '''
            <td>Description</td>
            <td>Acebutolol 100mg capsules (A A H Pharmaceuticals Ltd) 84 capsule</td>
            ''',
            html=True
        )
        self.assertContains(
            rsp,
            'This AMPP cannot be matched against our prescribing data'
        )


class TestSearchView(TestCase):
    fixtures = ['dmd-objs']

    def test_search_returning_no_results(self):
        rsp = self._get('bananas')

        # We expect to see "No results found".
        self.assertContains(rsp, 'No results found.')

    def test_search_by_returning_one_result(self):
        rsp = self._get('acebutolol', obj_types=['vmp'])

        # We expect to be redirected to the page for the one matching object.
        self.assertRedirects(rsp, '/dmd/vmp/318412000/')

    def test_search_returning_many_results(self):
        rsp = self._get('acebutolol')

        # We expect to see lists of the matching objects.
        self.assertContains(rsp, 'Virtual Medicinal Products (1)')
        self.assertContains(rsp, 'Acebutolol 100mg capsules')
        self.assertContains(rsp, 'Virtual Medicinal Product Packs (1)')
        self.assertContains(rsp, 'Acebutolol 100mg capsules 84 capsule')

    def test_search_for_all_obj_types_shows_limited_results(self):
        rsp = self._get(
            'acebutolol', 
            include=['invalid', 'unavailable', 'no_bnf_code'],
            max_results_per_obj_type=5,
        )

        # We expect to see 5 out of 6 of the AMPPs, and a link to show all of them.
        self.assertContains(rsp, 'Actual Medicinal Product Packs (6)')
        for supplier in [
            'A A H Pharmaceuticals Ltd',
            'Alliance Healthcare (Distribution) Ltd',
            'Kent Pharmaceuticals Ltd',
            'Phoenix Healthcare Distribution Ltd',
            'Sigma Pharmaceuticals Plc',
        ]:
            self.assertContains(rsp, supplier)
        self.assertNotContains(rsp, 'Waymade Healthcare Plc')
        self.assertContains(rsp, 'Show all Actual Medicinal Product Packs')

        # We don't expect to see a link to show all VMPPs, since there aren't
        # more than 5.
        self.assertNotContains(rsp, 'Show all Virtual Medicinal Product Packs')

    def test_search_for_one_obj_type_shows_all_results(self):
        rsp = self._get(
            'acebutolol', 
            obj_types=['ampp'],
            include=['invalid', 'unavailable', 'no_bnf_code'],
            max_results_per_obj_type=5,
        )

        # We expect to see all 6 AMPPs, and no link to show all of them.
        for supplier in [
            'A A H Pharmaceuticals Ltd',
            'Alliance Healthcare (Distribution) Ltd',
            'Kent Pharmaceuticals Ltd',
            'Phoenix Healthcare Distribution Ltd',
            'Sigma Pharmaceuticals Plc',
            'Waymade Healthcare Plc',
        ]:
            self.assertContains(rsp, supplier)

        self.assertNotContains(rsp, 'Show all Actual Medicinal Product Packs')

    def test_search_by_snomed_code_returning_one_result(self):
        rsp = self._get('318412000')

        # We expect to be redirected to the page for the one matching object.
        self.assertRedirects(rsp, '/dmd/vmp/318412000/')

    def test_search_by_snomed_code_returning_no_results(self):
        rsp = self._get('12345')

        # We expect to see "No results found".
        self.assertContains(rsp, 'No results found.')

    def test_with_invalid_form(self):
        rsp = self._get('aa')

        # We expect to see an error message because the search string was too short.
        self.assertContains(rsp, 'Ensure this value has at least')

        # We don't expect to see that a search has happened.
        self.assertNotContains(rsp, 'No results found.')

    def test_with_no_obj_types(self):
        rsp = self.client.get('/dmd/', {'q': 'acebutolol'})

        # We expect to see lists of the matching objects.
        self.assertContains(rsp, 'Virtual Medicinal Products (1)')
        self.assertContains(rsp, 'Acebutolol 100mg capsules')
        self.assertContains(rsp, 'Virtual Medicinal Product Packs (1)')
        self.assertContains(rsp, 'Acebutolol 100mg capsules 84 capsule')

    def _get(self, q, **extra_params):
        params = {
            'q': q,
            'obj_types': ['vtm', 'vmp', 'amp', 'vmpp', 'ampp'],
            'include': [],
        }
        params.update(extra_params)
        return self.client.get('/dmd/', params)
