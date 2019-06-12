import csv

from .api_test_base import ApiTestBase


class TestAPIOrgDetailsViews(ApiTestBase):
    def test_api_view_org_details_total(self):
        url = self.api_prefix
        url += '/org_details?format=csv'
        response = self.client.get(url, follow=True)
        self.assertEqual(response.status_code, 200)
        rows = list(csv.DictReader(response.content.splitlines()))
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]['date'], '2015-01-01')
        self.assertEqual(float(rows[0]['total_list_size']), 1260)
        self.assertEqual(rows[0]['astro_pu_cost'], '705.5')
        self.assertEqual(rows[0]['astro_pu_items'], '955.5')
        self.assertEqual(rows[0]['star_pu.oral_antibacterials_item'],
                         '95.5')

    def test_api_view_org_details_all_ccgs(self):
        url = self.api_prefix
        url += '/org_details?format=csv&org_type=ccg'
        response = self.client.get(url, follow=True)
        self.assertEqual(response.status_code, 200)
        rows = list(csv.DictReader(response.content.splitlines()))
        self.assertEqual(len(rows), 4)
        self.assertEqual(rows[1]['row_id'], '03V')
        self.assertEqual(rows[1]['row_name'], 'NHS Corby')
        self.assertEqual(rows[1]['date'], '2015-01-01')
        self.assertEqual(rows[1]['astro_pu_cost'], '363.3')
        self.assertEqual(rows[1]['astro_pu_items'], '453.3')
        self.assertEqual(rows[1]['star_pu.oral_antibacterials_item'],
                         '45.3')
        self.assertEqual(float(rows[1]['total_list_size']), 648)

    def test_api_view_org_details_all_ccgs_with_keys(self):
        url = self.api_prefix
        url += ('/org_details?format=csv&org_type=ccg&keys=total_list_size')
        response = self.client.get(url, follow=True)
        self.assertEqual(response.status_code, 200)
        rows = list(csv.DictReader(response.content.splitlines()))
        self.assertEqual(len(rows), 4)
        self.assertEqual(rows[1]['row_id'], '03V')
        self.assertEqual(rows[1]['row_name'], 'NHS Corby')
        self.assertEqual(rows[1]['date'], '2015-01-01')
        self.assertEqual(rows[1].get('astro_pu_cost'), None)
        self.assertEqual(float(rows[1]['total_list_size']), 648)

    def test_api_view_org_details_all_ccgs_with_nothing_key(self):
        url = self.api_prefix
        url += ('/org_details?format=csv&org_type=ccg&keys=nothing')
        response = self.client.get(url, follow=True)
        self.assertEqual(response.status_code, 200)
        list(csv.DictReader(response.content.splitlines()))

    def test_api_view_org_details_all_ccgs_with_unpermitted_key(self):
        url = self.api_prefix
        url += ('/org_details?format=csv&org_type=ccg&keys=borg')
        response = self.client.get(url, follow=True)
        self.assertEqual(response.status_code, 400)
        rows = list(csv.DictReader(response.content.splitlines()))
        self.assertEqual(rows[0]['detail'], 'borg is not a valid key')

    def test_api_view_org_details_all_ccgs_with_json_key(self):
        url = self.api_prefix
        url += ('/org_details?format=csv&org_type=ccg'
                '&keys=star_pu.oral_antibacterials_item,total_list_size')
        response = self.client.get(url, follow=True)
        self.assertEqual(response.status_code, 200)
        rows = list(csv.DictReader(response.content.splitlines()))
        self.assertEqual(rows[1]['row_id'], '03V')
        self.assertEqual(rows[1]['row_name'], 'NHS Corby')
        self.assertEqual(rows[1]['date'], '2015-01-01')
        self.assertEqual(rows[1]['star_pu.oral_antibacterials_item'],
                         '45.3')

    def test_api_view_org_details_one_ccg(self):
        url = self.api_prefix
        url += '/org_details?format=csv&org_type=ccg&org=03V'
        response = self.client.get(url, follow=True)
        self.assertEqual(response.status_code, 200)
        rows = list(csv.DictReader(response.content.splitlines()))
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]['row_id'], '03V')
        self.assertEqual(rows[0]['row_name'], 'NHS Corby')
        self.assertEqual(rows[0]['date'], '2015-01-01')
        self.assertEqual(rows[0]['astro_pu_cost'], '363.3')
        self.assertEqual(rows[0]['astro_pu_items'], '453.3')
        self.assertEqual(rows[0]['star_pu.oral_antibacterials_item'],
                         '45.3')
        self.assertEqual(float(rows[0]['total_list_size']), 648)

    def test_api_view_org_details_all_practices(self):
        url = self.api_prefix
        url += '/org_details?format=csv&org_type=practice'
        response = self.client.get(url, follow=True)
        self.assertEqual(response.status_code, 200)
        rows = list(csv.DictReader(response.content.splitlines()))
        self.assertEqual(len(rows), 10)  # 5 practices, 2 months
        self.assertEqual(rows[0]['row_id'], 'B82018')
        self.assertEqual(rows[0]['row_name'], 'ESCRICK SURGERY')
        self.assertEqual(rows[0]['date'], '2015-01-01')
        self.assertEqual(rows[0]['total_list_size'], '324')
        self.assertEqual(rows[0]['astro_pu_cost'], '181.1')
        self.assertEqual(rows[0]['astro_pu_items'], '271.1')
        self.assertEqual(rows[0]['star_pu.oral_antibacterials_item'], '27.1')

    def test_api_view_org_details_ccg_code_to_practices(self):
        # Practice K83622 moved from 03Q to 03V so we check that it is only
        # included in the results for 03V and not 03Q.
        url = self.api_prefix
        url += '/org_details?format=csv&org_type=practice&org=03V'
        response = self.client.get(url, follow=True)
        self.assertEqual(response.status_code, 200)
        rows = list(csv.DictReader(response.content.splitlines()))
        self.assertEqual(len(rows), 6)  # 3 practices, 2 months
        self.assertIn('K83622', [row['row_id'] for row in rows])
        self.assertEqual(rows[0]['row_id'], 'K83059')
        self.assertEqual(rows[0]['row_name'], 'DR KHALID & PARTNERS')
        self.assertEqual(rows[0]['date'], '2015-01-01')
        self.assertEqual(rows[0]['total_list_size'], '216')
        self.assertEqual(rows[0]['astro_pu_cost'], '121.1')
        self.assertEqual(rows[0]['astro_pu_items'], '151.1')
        self.assertEqual(rows[0]['star_pu.oral_antibacterials_item'], '15.1')

        url = self.api_prefix
        url += '/org_details?format=csv&org_type=practice&org=03Q'
        response = self.client.get(url, follow=True)
        self.assertEqual(response.status_code, 200)
        rows = list(csv.DictReader(response.content.splitlines()))
        self.assertEqual(len(rows), 4)  # 2 practices, 2 months
        self.assertNotIn('K83622', [row['row_id'] for row in rows])

    def test_api_view_org_details_one_practice(self):
        url = self.api_prefix
        url += '/org_details?format=csv&org_type=practice&org=N84014'
        response = self.client.get(url, follow=True)
        self.assertEqual(response.status_code, 200)
        rows = list(csv.DictReader(response.content.splitlines()))
        self.assertEqual(len(rows), 2)  # 2 months
        self.assertEqual(rows[0]['row_id'], 'N84014')
        self.assertEqual(rows[0]['row_name'], 'AINSDALE VILLAGE SURGERY')
        self.assertEqual(rows[0]['date'], '2015-01-01')
        self.assertEqual(rows[0]['total_list_size'], '288')
        self.assertEqual(rows[0]['astro_pu_cost'], '161.1')
        self.assertEqual(rows[0]['astro_pu_items'], '231.1')
        self.assertEqual(rows[0]['star_pu.oral_antibacterials_item'], '23.1')

    def test_api_view_org_details_one_practice_with_json_key(self):
        url = self.api_prefix
        url += ('/org_details?format=csv&org_type=practice&org=N84014'
                '&keys=star_pu.oral_antibacterials_item,total_list_size')
        response = self.client.get(url, follow=True)
        self.assertEqual(response.status_code, 200)
        rows = list(csv.DictReader(response.content.splitlines()))
        self.assertEqual(len(rows), 2)  # 2 months
        self.assertEqual(rows[0]['row_id'], 'N84014')
        self.assertEqual(rows[0]['row_name'], 'AINSDALE VILLAGE SURGERY')
        self.assertEqual(rows[0]['date'], '2015-01-01')
        self.assertEqual(rows[0]['total_list_size'], '288')
        self.assertEqual(rows[0]['star_pu.oral_antibacterials_item'], '23.1')
        self.assertEqual(rows[0].get('astro_pu_cost'), None)

    def test_api_view_org_details_all_nhs_with_json_key(self):
        url = self.api_prefix
        url += ('/org_details?format=csv'
                '&keys=star_pu.oral_antibacterials_item,total_list_size')
        response = self.client.get(url, follow=True)
        self.assertEqual(response.status_code, 200)
        rows = list(csv.DictReader(response.content.splitlines()))
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]['date'], '2015-01-01')
        self.assertEqual(float(rows[0]['total_list_size']), 1260)
        self.assertEqual(rows[0]['star_pu.oral_antibacterials_item'],
                         '95.5')
        self.assertEqual(rows[0].get('astro_pu_cost'), None)
