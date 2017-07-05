import csv

from .api_test_base import ApiTestBase


class TestAPIOrgDetailsViews(ApiTestBase):
    def test_api_view_org_details_total(self):
        url = self.api_prefix
        url += '/org_details?format=csv'
        response = self.client.get(url, follow=True)
        self.assertEqual(response.status_code, 200)
        reader = csv.DictReader(response.content.splitlines())
        rows = []
        for row in reader:
            rows.append(row)
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]['date'], '2015-01-01')
        self.assertEqual(float(rows[0]['total_list_size']), 53)
        self.assertEqual(rows[0]['astro_pu_cost'], '695.4')
        self.assertEqual(rows[0]['astro_pu_items'], '1219.4')
        self.assertEqual(rows[0]['star_pu.oral_antibacterials_item'],
                         '45.2')

    def test_api_view_org_details_all_ccgs(self):
        url = self.api_prefix
        url += '/org_details?format=csv&org_type=ccg'
        response = self.client.get(url, follow=True)
        self.assertEqual(response.status_code, 200)
        reader = csv.DictReader(response.content.splitlines())
        rows = []
        for row in reader:
            rows.append(row)
        self.assertEqual(len(rows), 3)
        self.assertEqual(rows[1]['row_id'], '03V')
        self.assertEqual(rows[1]['row_name'], 'NHS Corby')
        self.assertEqual(rows[1]['date'], '2015-01-01')
        self.assertEqual(rows[1]['astro_pu_cost'], '205.7')
        self.assertEqual(rows[1]['astro_pu_items'], '400.2')
        self.assertEqual(rows[1]['star_pu.oral_antibacterials_item'],
                         '35.2')
        self.assertEqual(float(rows[1]['total_list_size']), 28)

    def test_api_view_org_details_all_ccgs_with_keys(self):
        url = self.api_prefix
        url += ('/org_details?format=csv&org_type=ccg&keys=total_list_size')
        response = self.client.get(url, follow=True)
        self.assertEqual(response.status_code, 200)
        reader = csv.DictReader(response.content.splitlines())
        rows = []
        for row in reader:
            rows.append(row)
        self.assertEqual(len(rows), 3)
        self.assertEqual(rows[1]['row_id'], '03V')
        self.assertEqual(rows[1]['row_name'], 'NHS Corby')
        self.assertEqual(rows[1]['date'], '2015-01-01')
        self.assertEqual(rows[1].get('astro_pu_cost'), None)
        self.assertEqual(float(rows[1]['total_list_size']), 28)

    def test_api_view_org_details_all_ccgs_with_unpermitted_key(self):
        url = self.api_prefix
        url += ('/org_details?format=csv&org_type=ccg&keys=borg')
        response = self.client.get(url, follow=True)
        self.assertEqual(response.status_code, 400)
        reader = csv.DictReader(response.content.splitlines())
        rows = []
        for row in reader:
            rows.append(row)
        self.assertEqual(rows[0]['detail'], 'borg is not a valid key')

    def test_api_view_org_details_all_ccgs_with_json_key(self):
        url = self.api_prefix
        url += ('/org_details?format=csv&org_type=ccg'
                '&keys=star_pu.oral_antibacterials_item,total_list_size')
        response = self.client.get(url, follow=True)
        self.assertEqual(response.status_code, 200)
        reader = csv.DictReader(response.content.splitlines())
        rows = []
        for row in reader:
            rows.append(row)
        self.assertEqual(rows[1]['row_id'], '03V')
        self.assertEqual(rows[1]['row_name'], 'NHS Corby')
        self.assertEqual(rows[1]['date'], '2015-01-01')
        self.assertEqual(rows[1]['star_pu.oral_antibacterials_item'],
                         '35.2')

    def test_api_view_org_details_one_ccg(self):
        url = self.api_prefix
        url += '/org_details?format=csv&org_type=ccg&org=03V'
        response = self.client.get(url, follow=True)
        self.assertEqual(response.status_code, 200)
        reader = csv.DictReader(response.content.splitlines())
        rows = []
        for row in reader:
            rows.append(row)
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]['row_id'], '03V')
        self.assertEqual(rows[0]['row_name'], 'NHS Corby')
        self.assertEqual(rows[0]['date'], '2015-01-01')
        self.assertEqual(rows[0]['astro_pu_cost'], '205.7')
        self.assertEqual(rows[0]['astro_pu_items'], '400.2')
        self.assertEqual(rows[0]['star_pu.oral_antibacterials_item'],
                         '35.2')
        self.assertEqual(float(rows[0]['total_list_size']), 28)

    def test_api_view_org_details_all_practices(self):
        url = self.api_prefix
        url += '/org_details?format=csv&org_type=practice'
        response = self.client.get(url, follow=True)
        self.assertEqual(response.status_code, 200)
        reader = csv.DictReader(response.content.splitlines())
        rows = []
        for row in reader:
            rows.append(row)
        self.assertEqual(len(rows), 4)
        self.assertEqual(rows[0]['row_id'], 'N84014')
        self.assertEqual(rows[0]['row_name'], 'AINSDALE VILLAGE SURGERY')
        self.assertEqual(rows[0]['date'], '2015-01-01')
        self.assertEqual(float(rows[0]['total_list_size']), 25)
        self.assertEqual(rows[0]['astro_pu_cost'], '489.7')
        self.assertEqual(rows[0]['astro_pu_items'], '819.2')
        self.assertEqual(rows[0]['star_pu.oral_antibacterials_item'],
                         '10')
        self.assertEqual(rows[3]['row_id'], 'P87629')
        self.assertEqual(rows[3]['date'], '2015-02-01')
        self.assertEqual(float(rows[3]['total_list_size']), 29)
        self.assertEqual(rows[3]['astro_pu_items'], '1600.2')
        self.assertEqual(rows[3]['star_pu.oral_antibacterials_item'],
                         '29')

    def test_api_view_org_details_ccg_code_to_practices(self):
        url = self.api_prefix
        url += '/org_details?format=csv&org_type=practice&org=03Q'
        response = self.client.get(url, follow=True)
        self.assertEqual(response.status_code, 200)
        reader = csv.DictReader(response.content.splitlines())
        rows = []
        for row in reader:
            rows.append(row)
        # Although in the practicestatistics fixtures, N84014 was in
        # 03Q in only one month, we want to return all practices as if
        # they were always in their current CCG membership
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]['row_id'], 'N84014')
        self.assertEqual(rows[0]['row_name'], 'AINSDALE VILLAGE SURGERY')
        self.assertEqual(rows[0]['date'], '2015-01-01')
        self.assertEqual(float(rows[0]['total_list_size']), 25)
        self.assertEqual(rows[0]['astro_pu_cost'], '489.7')
        self.assertEqual(rows[0]['astro_pu_items'], '819.2')
        self.assertEqual(rows[0]['star_pu.oral_antibacterials_item'],
                         '10')

    def test_api_view_org_details_one_practice(self):
        url = self.api_prefix
        url += '/org_details?format=csv&org_type=practice&org=N84014'
        response = self.client.get(url, follow=True)
        self.assertEqual(response.status_code, 200)
        reader = csv.DictReader(response.content.splitlines())
        rows = []
        for row in reader:
            rows.append(row)
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]['row_id'], 'N84014')
        self.assertEqual(rows[0]['row_name'], 'AINSDALE VILLAGE SURGERY')
        self.assertEqual(rows[0]['date'], '2015-01-01')
        self.assertEqual(float(rows[0]['total_list_size']), 25)
        self.assertEqual(rows[0]['astro_pu_cost'], '489.7')
        self.assertEqual(rows[0]['astro_pu_items'], '819.2')
        self.assertEqual(rows[0]['star_pu.oral_antibacterials_item'],
                         '10')

    def test_api_view_org_details_one_practice_with_json_key(self):
        url = self.api_prefix
        url += ('/org_details?format=csv&org_type=practice&org=N84014'
                '&keys=star_pu.oral_antibacterials_item,total_list_size')
        response = self.client.get(url, follow=True)
        self.assertEqual(response.status_code, 200)
        reader = csv.DictReader(response.content.splitlines())
        rows = []
        for row in reader:
            rows.append(row)
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]['row_id'], 'N84014')
        self.assertEqual(rows[0]['row_name'], 'AINSDALE VILLAGE SURGERY')
        self.assertEqual(rows[0]['date'], '2015-01-01')
        self.assertEqual(float(rows[0]['total_list_size']), 25)
        self.assertEqual(rows[0]['star_pu.oral_antibacterials_item'],
                         '10')
        self.assertEqual(rows[0].get('astro_pu_cost'), None)

    def test_api_view_org_details_all_nhs_with_json_key(self):
        url = self.api_prefix
        url += ('/org_details?format=csv'
                '&keys=star_pu.oral_antibacterials_item,total_list_size')
        response = self.client.get(url, follow=True)
        self.assertEqual(response.status_code, 200)
        reader = csv.DictReader(response.content.splitlines())
        rows = []
        for row in reader:
            rows.append(row)
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]['date'], '2015-01-01')
        self.assertEqual(float(rows[0]['total_list_size']), 53)
        self.assertEqual(rows[0]['star_pu.oral_antibacterials_item'],
                         '45.2')
        self.assertEqual(rows[0].get('astro_pu_cost'), '695.4')
