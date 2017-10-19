import datetime
import json

from django.db import connection

from .api_test_base import ApiTestBase

from frontend.models import ImportLog


def _create_prescribing_tables():
    current = datetime.date(2013, 4, 1)
    cmd = ("DROP TABLE IF EXISTS %s; "
           "CREATE TABLE %s () INHERITS (frontend_prescription)")
    with connection.cursor() as cursor:
        for _ in range(0, 59):
            table_name = "frontend_prescription_%s%s" % (
                current.year, str(current.month).zfill(2))
            cursor.execute(cmd % (table_name, table_name))
            current = datetime.date(current.year + (current.month / 12),
                                    ((current.month % 12) + 1), 1)
    ImportLog.objects.create(current_at=current, category='prescribing')


class TestAPISpendingViews(ApiTestBase):
    def test_codes_are_rejected_if_not_same_length(self):
        url = '%s/spending' % self.api_prefix
        url += '?format=csv&code=0202010B0,0202010B0AAAAAA'
        response = self.client.get(url, follow=True)
        self.assertEqual(response.status_code, 400)

    def test_404_returned_for_unknown_short_code(self):
        url = '%s/spending?format=csv&code=0' % self.api_prefix
        response = self.client.get(url, follow=True)
        self.assertEqual(response.status_code, 404)

    def test_404_returned_for_unknown_dotted_code(self):
        url = '%s/spending?format=csv&code=123.456' % self.api_prefix
        response = self.client.get(url, follow=True)
        self.assertEqual(response.status_code, 404)

    ########################################
    # Spending across all NHS England.
    ########################################
    def test_total_spending(self):
        _create_prescribing_tables()
        rows = self._rows_from_api('/spending?format=csv')
        self.assertEqual(len(rows), 60)
        self.assertEqual(rows[0]['date'], '2013-04-01')
        self.assertEqual(rows[0]['actual_cost'], '4.61')
        self.assertEqual(rows[0]['items'], '3')
        self.assertEqual(rows[0]['quantity'], '82')
        self.assertEqual(rows[1]['date'], '2013-05-01')
        self.assertEqual(rows[1]['actual_cost'], '0.0')
        self.assertEqual(rows[1]['items'], '0')
        self.assertEqual(rows[1]['quantity'], '0')
        self.assertEqual(rows[19]['date'], '2014-11-01')
        self.assertEqual(rows[19]['actual_cost'], '90.54')
        self.assertEqual(rows[19]['items'], '95')
        self.assertEqual(rows[19]['quantity'], '5142')

    def test_total_spending_by_bnf_section(self):
        _create_prescribing_tables()
        rows = self._rows_from_api('/spending?format=csv&code=2')
        self.assertEqual(rows[0]['date'], '2013-04-01')
        self.assertEqual(rows[0]['actual_cost'], '4.61')
        self.assertEqual(rows[0]['items'], '3')
        self.assertEqual(rows[0]['quantity'], '82')
        self.assertEqual(rows[19]['date'], '2014-11-01')
        self.assertEqual(rows[19]['actual_cost'], '90.54')
        self.assertEqual(rows[19]['items'], '95')
        self.assertEqual(rows[19]['quantity'], '5142')

    def test_total_spending_by_bnf_section_full_code(self):
        _create_prescribing_tables()
        rows = self._rows_from_api('/spending?format=csv&code=02')
        self.assertEqual(rows[0]['date'], '2013-04-01')
        self.assertEqual(rows[0]['actual_cost'], '4.61')
        self.assertEqual(rows[0]['items'], '3')
        self.assertEqual(rows[0]['quantity'], '82')
        self.assertEqual(rows[19]['date'], '2014-11-01')
        self.assertEqual(rows[19]['actual_cost'], '90.54')
        self.assertEqual(rows[19]['items'], '95')
        self.assertEqual(rows[19]['quantity'], '5142')

    def test_total_spending_by_code(self):
        _create_prescribing_tables()
        rows = self._rows_from_api('/spending?format=csv&code=0204000I0')
        self.assertEqual(rows[19]['date'], '2014-11-01')
        self.assertEqual(rows[19]['actual_cost'], '36.28')
        self.assertEqual(rows[19]['items'], '33')
        self.assertEqual(rows[19]['quantity'], '2354')

    def test_total_spending_by_codes(self):
        _create_prescribing_tables()
        url = '/spending?format=csv'
        url += '&code=0204000I0,0202010B0'
        rows = self._rows_from_api(url)
        self.assertEqual(rows[17]['date'], '2014-09-01')
        self.assertEqual(rows[17]['actual_cost'], '36.29')
        self.assertEqual(rows[17]['items'], '40')
        self.assertEqual(rows[17]['quantity'], '1209')

    ########################################
    # Total spending by CCG.
    ########################################
    def test_total_spending_by_ccg(self):
        rows = self._rows_from_api('/spending_by_ccg?format=csv')
        self.assertEqual(len(rows), 9)
        self.assertEqual(rows[6]['row_id'], '03V')
        self.assertEqual(rows[6]['row_name'], 'NHS Corby')
        self.assertEqual(rows[6]['date'], '2014-09-01')
        self.assertEqual(rows[6]['actual_cost'], '38.28')
        self.assertEqual(rows[6]['items'], '41')
        self.assertEqual(rows[6]['quantity'], '1241')

    def test_total_spending_by_one_ccg(self):
        rows = self._rows_from_api('/spending_by_ccg?format=csv&org=03V')
        self.assertEqual(len(rows), 5)
        self.assertEqual(rows[-2]['row_id'], '03V')
        self.assertEqual(rows[-2]['row_name'], 'NHS Corby')
        self.assertEqual(rows[-2]['date'], '2014-09-01')
        self.assertEqual(rows[-2]['actual_cost'], '38.28')
        self.assertEqual(rows[-2]['items'], '41')
        self.assertEqual(rows[-2]['quantity'], '1241')

    def test_total_spending_by_multiple_ccgs(self):
        rows = self._rows_from_api('/spending_by_ccg?format=csv&org=03V,03Q')
        self.assertEqual(len(rows), 9)
        self.assertEqual(rows[6]['row_id'], '03V')
        self.assertEqual(rows[6]['row_name'], 'NHS Corby')
        self.assertEqual(rows[6]['date'], '2014-09-01')
        self.assertEqual(rows[6]['actual_cost'], '38.28')
        self.assertEqual(rows[6]['items'], '41')
        self.assertEqual(rows[6]['quantity'], '1241')

    def test_spending_by_all_ccgs_on_chemical(self):
        rows = self._rows_from_api(
            '/spending_by_ccg?format=csv&code=0202010B0')
        self.assertEqual(len(rows), 6)
        self.assertEqual(rows[0]['row_id'], '03V')
        self.assertEqual(rows[0]['row_name'], 'NHS Corby')
        self.assertEqual(rows[0]['date'], '2013-04-01')
        self.assertEqual(rows[0]['actual_cost'], '1.56')
        self.assertEqual(rows[0]['items'], '1')
        self.assertEqual(rows[0]['quantity'], '26')
        self.assertEqual(rows[5]['row_id'], '03V')
        self.assertEqual(rows[5]['row_name'], 'NHS Corby')
        self.assertEqual(rows[5]['date'], '2014-11-01')
        self.assertEqual(rows[5]['actual_cost'], '54.26')
        self.assertEqual(rows[5]['items'], '62')
        self.assertEqual(rows[5]['quantity'], '2788')

    def test_spending_by_all_ccgs_on_multiple_chemicals(self):
        url = '/spending_by_ccg'
        url += '?format=csv&code=0202010B0,0202010F0'
        rows = self._rows_from_api(url)
        self.assertEqual(len(rows), 9)
        self.assertEqual(rows[0]['row_id'], '03Q')
        self.assertEqual(rows[0]['row_name'], 'NHS Vale of York')
        self.assertEqual(rows[0]['date'], '2013-04-01')
        self.assertEqual(rows[0]['actual_cost'], '3.05')
        self.assertEqual(rows[0]['items'], '2')
        self.assertEqual(rows[0]['quantity'], '56')
        self.assertEqual(rows[-3]['row_id'], '03V')
        self.assertEqual(rows[-3]['row_name'], 'NHS Corby')
        self.assertEqual(rows[-3]['date'], '2014-09-01')
        self.assertEqual(rows[-3]['actual_cost'], '38.28')
        self.assertEqual(rows[-3]['items'], '41')
        self.assertEqual(rows[-3]['quantity'], '1241')

    def test_spending_by_all_ccgs_on_product(self):
        url = '/spending_by_ccg'
        url += '?format=csv&code=0204000I0BC'
        rows = self._rows_from_api(url)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]['row_id'], '03V')
        self.assertEqual(rows[0]['row_name'], 'NHS Corby')
        self.assertEqual(rows[0]['date'], '2014-11-01')
        self.assertEqual(rows[0]['actual_cost'], '32.26')
        self.assertEqual(rows[0]['items'], '29')
        self.assertEqual(rows[0]['quantity'], '2350')

    def test_spending_by_all_ccgs_on_presentation(self):
        url = '/spending_by_ccg'
        url += '?format=csv&code=0202010B0AAABAB'
        rows = self._rows_from_api(url)
        self.assertEqual(len(rows), 3)
        self.assertEqual(rows[2]['row_id'], '03V')
        self.assertEqual(rows[2]['row_name'], 'NHS Corby')
        self.assertEqual(rows[2]['date'], '2014-11-01')
        self.assertEqual(rows[2]['actual_cost'], '54.26')
        self.assertEqual(rows[2]['items'], '62')
        self.assertEqual(rows[2]['quantity'], '2788')

    def test_spending_by_all_ccgs_on_multiple_presentations(self):
        url = '/spending_by_ccg'
        url += '?format=csv&code=0202010F0AAAAAA,0202010B0AAACAC'
        rows = self._rows_from_api(url)
        self.assertEqual(len(rows), 7)
        self.assertEqual(rows[0]['row_id'], '03Q')
        self.assertEqual(rows[0]['row_name'], 'NHS Vale of York')
        self.assertEqual(rows[0]['date'], '2013-04-01')
        self.assertEqual(rows[0]['actual_cost'], '3.05')
        self.assertEqual(rows[0]['items'], '2')
        self.assertEqual(rows[0]['quantity'], '56')

    def test_spending_by_all_ccgs_on_bnf_section(self):
        url = '/spending_by_ccg?format=csv&code=2.2.1'
        rows = self._rows_from_api(url)
        self.assertEqual(len(rows), 9)
        self.assertEqual(rows[0]['row_id'], '03Q')
        self.assertEqual(rows[0]['row_name'], 'NHS Vale of York')
        self.assertEqual(rows[0]['date'], '2013-04-01')
        self.assertEqual(rows[0]['actual_cost'], '3.05')
        self.assertEqual(rows[0]['items'], '2')
        self.assertEqual(rows[0]['quantity'], '56')
        self.assertEqual(rows[-1]['row_id'], '03V')
        self.assertEqual(rows[-1]['row_name'], 'NHS Corby')
        self.assertEqual(rows[-1]['date'], '2014-11-01')
        self.assertEqual(rows[-1]['actual_cost'], '54.26')
        self.assertEqual(rows[-1]['items'], '62')
        self.assertEqual(rows[-1]['quantity'], '2788')

    def test_spending_by_all_ccgs_on_multiple_bnf_sections(self):
        url = '/spending_by_ccg?format=csv&code=2.2,2.4'
        rows = self._rows_from_api(url)
        self.assertEqual(len(rows), 9)
        self.assertEqual(rows[-1]['row_id'], '03V')
        self.assertEqual(rows[-1]['row_name'], 'NHS Corby')
        self.assertEqual(rows[-1]['date'], '2014-11-01')
        self.assertEqual(rows[-1]['actual_cost'], '90.54')
        self.assertEqual(rows[-1]['items'], '95')
        self.assertEqual(rows[-1]['quantity'], '5142')

    ########################################
    # Total spending by practice.
    ########################################
    def test_spending_by_all_practices_on_product_without_date(self):
        url = '%s/spending_by_practice' % self.api_prefix
        url += '?format=csv&code=0204000I0BC'
        response = self.client.get(url, follow=True)
        self.assertEqual(response.status_code, 400)

    def test_total_spending_by_practice(self):
        url = '/spending_by_practice'
        url += '?format=csv&date=2014-11-01'
        rows = self._rows_from_api(url)
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]['row_id'], 'K83059')
        self.assertEqual(rows[0]['row_name'], 'DR KHALID & PARTNERS')
        self.assertEqual(rows[0]['date'], '2014-11-01')
        self.assertEqual(rows[0]['setting'], '-1')
        self.assertEqual(rows[0]['ccg'], '03V')
        self.assertEqual(rows[0]['actual_cost'], '26.28')
        self.assertEqual(rows[0]['items'], '40')
        self.assertEqual(rows[0]['quantity'], '2543')

    def test_spending_by_practice_on_chemical(self):
        url = '/spending_by_practice'
        url += '?format=csv&code=0204000I0&date=2014-11-01'
        rows = self._rows_from_api(url)
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]['row_id'], 'K83059')
        self.assertEqual(rows[0]['row_name'], 'DR KHALID & PARTNERS')
        self.assertEqual(rows[0]['setting'], '-1')
        self.assertEqual(rows[0]['ccg'], '03V')
        self.assertEqual(rows[0]['date'], '2014-11-01')
        self.assertEqual(rows[0]['actual_cost'], '14.15')
        self.assertEqual(rows[0]['items'], '16')
        self.assertEqual(rows[0]['quantity'], '1154')

    def test_spending_by_all_practices_on_chemical_with_date(self):
        url = '/spending_by_practice'
        url += '?format=csv&code=0202010F0&date=2014-09-01'
        rows = self._rows_from_api(url)
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]['row_id'], 'N84014')
        self.assertEqual(rows[0]['actual_cost'], '11.99')
        self.assertEqual(rows[0]['items'], '1')
        self.assertEqual(rows[0]['quantity'], '128')
        self.assertEqual(rows[1]['row_id'], 'P87629')
        self.assertEqual(rows[1]['actual_cost'], '1.99')
        self.assertEqual(rows[1]['items'], '1')
        self.assertEqual(rows[1]['quantity'], '32')

    def test_spending_by_one_practice(self):
        url = '/spending_by_practice?format=csv&org=P87629'
        rows = self._rows_from_api(url)
        self.assertEqual(len(rows), 5)
        self.assertEqual(rows[-1]['row_id'], 'P87629')
        self.assertEqual(rows[-1]['row_name'], '1/ST ANDREWS MEDICAL PRACTICE')
        self.assertEqual(rows[-1]['date'], '2014-11-01')
        self.assertEqual(rows[-1]['actual_cost'], '64.26')
        self.assertEqual(rows[-1]['items'], '55')
        self.assertEqual(rows[-1]['quantity'], '2599')

    def test_spending_by_one_practice_on_chemical(self):
        url = '/spending_by_practice'
        url += '?format=csv&code=0202010B0&org=P87629'
        rows = self._rows_from_api(url)
        self.assertEqual(len(rows), 5)
        self.assertEqual(rows[-1]['row_id'], 'P87629')
        self.assertEqual(rows[-1]['row_name'], '1/ST ANDREWS MEDICAL PRACTICE')
        self.assertEqual(rows[-1]['setting'], '4')
        self.assertEqual(rows[-1]['ccg'], '03V')
        self.assertEqual(rows[-1]['date'], '2014-11-01')
        self.assertEqual(rows[-1]['actual_cost'], '42.13')
        self.assertEqual(rows[-1]['items'], '38')
        self.assertEqual(rows[-1]['quantity'], '1399')

    def test_spending_by_practice_on_multiple_chemicals(self):
        url = '/spending_by_practice?format=csv'
        url += '&code=0202010B0,0204000I0&org=P87629,K83059'
        rows = self._rows_from_api(url)
        self.assertEqual(len(rows), 6)
        self.assertEqual(rows[2]['row_id'], 'P87629')
        self.assertEqual(rows[2]['row_name'], '1/ST ANDREWS MEDICAL PRACTICE')
        self.assertEqual(rows[2]['date'], '2013-10-01')
        self.assertEqual(rows[2]['actual_cost'], '1.62')
        self.assertEqual(rows[2]['items'], '1')
        self.assertEqual(rows[2]['quantity'], '24')

    def test_spending_by_all_practices_on_product(self):
        url = '/spending_by_practice'
        url += '?format=csv&code=0202010B0AA&date=2014-11-01'
        rows = self._rows_from_api(url)
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]['row_id'], 'K83059')
        self.assertEqual(rows[0]['actual_cost'], '12.13')
        self.assertEqual(rows[0]['items'], '24')
        self.assertEqual(rows[0]['quantity'], '1389')
        self.assertEqual(rows[1]['row_id'], 'P87629')
        self.assertEqual(rows[1]['actual_cost'], '42.13')
        self.assertEqual(rows[1]['items'], '38')
        self.assertEqual(rows[1]['quantity'], '1399')

    def test_spending_by_all_practices_on_presentation(self):
        url = '/spending_by_practice'
        url += '?format=csv&code=0202010B0AAABAB&date=2014-11-01'
        rows = self._rows_from_api(url)
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]['row_id'], 'K83059')
        self.assertEqual(rows[0]['actual_cost'], '12.13')
        self.assertEqual(rows[0]['items'], '24')
        self.assertEqual(rows[0]['quantity'], '1389')
        self.assertEqual(rows[1]['row_id'], 'P87629')
        self.assertEqual(rows[1]['actual_cost'], '42.13')
        self.assertEqual(rows[1]['items'], '38')
        self.assertEqual(rows[1]['quantity'], '1399')

    def test_spending_by_practice_on_presentation(self):
        url = '/spending_by_practice'
        url += '?format=csv&code=0204000I0BCAAAB&org=03V'
        rows = self._rows_from_api(url)
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[1]['row_id'], 'P87629')
        self.assertEqual(rows[1]['row_name'], '1/ST ANDREWS MEDICAL PRACTICE')
        self.assertEqual(rows[1]['setting'], '4')
        self.assertEqual(rows[1]['ccg'], '03V')
        self.assertEqual(rows[1]['date'], '2014-11-01')
        self.assertEqual(rows[1]['actual_cost'], '22.13')
        self.assertEqual(rows[1]['items'], '17')
        self.assertEqual(rows[1]['quantity'], '1200')

    def test_spending_by_practice_on_multiple_presentations(self):
        url = '/spending_by_practice'
        url += '?format=csv&code=0204000I0BCAAAB,0202010B0AAABAB&org=03V'
        rows = self._rows_from_api(url)
        self.assertEqual(len(rows), 3)
        self.assertEqual(rows[2]['row_id'], 'P87629')
        self.assertEqual(rows[2]['row_name'], '1/ST ANDREWS MEDICAL PRACTICE')
        self.assertEqual(rows[2]['date'], '2014-11-01')
        self.assertEqual(rows[2]['actual_cost'], '64.26')
        self.assertEqual(rows[2]['items'], '55')
        self.assertEqual(rows[2]['quantity'], '2599')

    def test_spending_by_practice_on_section(self):
        url = '/spending_by_practice'
        url += '?format=csv&code=2&org=03V'
        rows = self._rows_from_api(url)
        self.assertEqual(len(rows), 6)
        self.assertEqual(rows[-1]['row_id'], 'P87629')
        self.assertEqual(rows[-1]['row_name'], '1/ST ANDREWS MEDICAL PRACTICE')
        self.assertEqual(rows[-1]['date'], '2014-11-01')
        self.assertEqual(rows[-1]['actual_cost'], '64.26')
        self.assertEqual(rows[-1]['items'], '55')
        self.assertEqual(rows[-1]['quantity'], '2599')

    def test_spending_by_practice_on_multiple_sections(self):
        url = '/spending_by_practice'
        url += '?format=csv&code=0202,0204&org=03Q'
        rows = self._rows_from_api(url)
        self.assertEqual(len(rows), 4)
        self.assertEqual(rows[0]['row_id'], 'N84014')
        self.assertEqual(rows[0]['row_name'], 'AINSDALE VILLAGE SURGERY')
        self.assertEqual(rows[0]['date'], '2013-04-01')
        self.assertEqual(rows[0]['actual_cost'], '3.05')
        self.assertEqual(rows[0]['items'], '2')
        self.assertEqual(rows[0]['quantity'], '56')


class TestAPISpendingViewsPPUTable(ApiTestBase):
    fixtures = ApiTestBase.fixtures + ['ppusavings', 'dmdproducts']

    def test_simple(self):
        url = '/price_per_unit?format=json'
        url += '&bnf_code=0202010F0AAAAAA&date=2014-11-01'
        url = self.api_prefix + url
        response = self.client.get(url, follow=True)
        data = json.loads(response.content)
        expected = {
            "lowest_decile": 0.1,
            "presentation": "0202010F0AAAAAA",
            "name": "Verapamil 160mg tablets",
            "price_per_unit": 0.2,
            "flag_bioequivalence": False,
            "practice": "P87629",
            "formulation_swap": None,
            "pct": None,
            "practice_name": "1/ST Andrews Medical Practice",
            "date": "2014-11-01",
            "quantity": 1,
            "id": 5,
            "possible_savings": 100.0
        }
        self.assertEqual(data[0], expected)


class TestAPISpendingViewsPPUBubble(ApiTestBase):
    fixtures = ApiTestBase.fixtures + ['importlog']

    def test_simple(self):
        url = '/bubble?format=json'
        url += '&bnf_code=0204000I0BCAAAB&date=2014-11-01&highlight=03V'
        url = self.api_prefix + url
        response = self.client.get(url, follow=True)
        data = json.loads(response.content)
        self.assertEqual(len(data['series']), 1)  # Only Trandate prescribed
        self.assertEqual(len([x for x in data if x[1]]), 3)

    def test_date(self):
        url = '/bubble?format=json'
        url += '&bnf_code=0204000I0BCAAAB&date=2000-01-01&highlight=03V'
        url = self.api_prefix + url
        response = self.client.get(url, follow=True)
        data = json.loads(response.content)
        self.assertEqual(len(data['series']), 0)

    def test_highlight(self):
        url = '/bubble?format=json'
        url += '&bnf_code=0204000I0BCAAAB&date=2014-11-01&highlight=03V'
        url = self.api_prefix + url
        response = self.client.get(url, follow=True)
        data = json.loads(response.content)
        # N.B. This is the mean of a *single* value; although there
        # are two values in the raw data, one is trimmed as it is
        # outside the 99th percentile
        self.assertEqual(data['plotline'], 0.0325)

    def test_code_without_matches(self):
        url = '/bubble?format=json'
        url += '&bnf_code=0204000I0BCAAAX&date=2014-11-01&highlight=03V'
        url = self.api_prefix + url
        response = self.client.get(url, follow=True)
        data = json.loads(response.content)
        self.assertIsNone(data['plotline'])

    def test_focus(self):
        url = '/bubble?format=json'
        url += '&bnf_code=0202010F0AAAAAA&date=2014-09-01'
        url += '&highlight=03V&focus=1'
        url = self.api_prefix + url
        response = self.client.get(url, follow=True)
        data = json.loads(response.content)
        self.assertEqual(data, {
            'series': [{
                'y': 0.09,
                'x': 1,
                'z': 32.0,
                'name': 'Chlortalidone_Tab 50mg',
                'mean_ppu': 0.09
            }],
            'categories': [{
                'is_generic': True,
                'name': 'Chlortalidone_Tab 50mg'
            }],
            'plotline':
            0.08875
        })

    def test_no_focus(self):
        url = '/bubble?format=json'
        url += '&bnf_code=0202010F0AAAAAA&date=2014-09-01'
        url += '&highlight=03V'
        url = self.api_prefix + url
        response = self.client.get(url, follow=True)
        data = json.loads(response.content)
        self.assertEqual(data, {
            'series': [{
                'y': 0.09,
                'x': 1,
                'z': 32.0,
                'name': 'Chlortalidone_Tab 50mg',
                'mean_ppu': 0.095
            }, {
                'y': 0.1,
                'x': 1,
                'z': 128.0,
                'name': 'Chlortalidone_Tab 50mg',
                'mean_ppu': 0.095
            }],
            'categories': [{
                'is_generic': True,
                'name': 'Chlortalidone_Tab 50mg'
            }],
            'plotline':
            0.08875
        })

    def test_trim(self):
        url = '/bubble?format=json'
        url += '&bnf_code=0202010F0AAAAAA&date=2014-09-01'
        url += '&highlight=03V&trim=1'
        url = self.api_prefix + url
        response = self.client.get(url, follow=True)
        data = json.loads(response.content)
        self.assertEqual(data, {
            'series': [{
                'y': 0.09,
                'x': 1,
                'z': 32.0,
                'name': 'Chlortalidone_Tab 50mg',
                'mean_ppu': 0.095
            }],
            'categories': [{
                'is_generic': True,
                'name': 'Chlortalidone_Tab 50mg'
            }],
            'plotline':
            0.08875
        })


class TestAPISpendingViewsPPUWithGenericMapping(ApiTestBase):
    fixtures = ApiTestBase.fixtures + ['importlog', 'genericcodemapping']

    def test_with_wildcard(self):
        url = '/bubble?format=json'
        url += '&bnf_code=0204000I0BCAAAB&date=2014-11-01&highlight=03V'
        url = self.api_prefix + url
        response = self.client.get(url, follow=True)
        data = json.loads(response.content)
        # Expecting the total to be quite different
        self.assertEqual(data['plotline'], 0.0315505963832243)
        # Bendroflumethiazide and Trandate:
        self.assertEqual(len(data['series']), 2)

    def test_with_specific(self):
        url = '/bubble?format=json'
        url += '&bnf_code=0204000I0BCAAAX&date=2014-11-01&highlight=03V'
        url = self.api_prefix + url
        response = self.client.get(url, follow=True)
        data = json.loads(response.content)
        self.assertEqual(data['plotline'], 0.0325)
