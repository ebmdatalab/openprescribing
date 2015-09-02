import csv
import os
import json
import unittest
from django.core import management
from django.test import TestCase
from common import utils


def setUpModule():
    fix_dir = 'frontend/tests/fixtures/'
    management.call_command('loaddata', fix_dir + 'chemicals.json',
                            verbosity=0)
    management.call_command('loaddata', fix_dir + 'sections.json',
                            verbosity=0)
    management.call_command('loaddata', fix_dir + 'ccgs.json',
                            verbosity=0)
    management.call_command('loaddata', fix_dir + 'practices.json',
                            verbosity=0)
    management.call_command('loaddata', fix_dir + 'shas.json',
                            verbosity=0)
    management.call_command('loaddata', fix_dir + 'practice_listsizes.json',
                            verbosity=0)


def tearDownModule():
    management.call_command('flush', verbosity=0, interactive=False)


class TestAPIOrgDetailsViews(TestCase):

    api_prefix = '/api/1.0'

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
        self.assertEqual(rows[0]['total_list_size'], '53')
        self.assertEqual(rows[0]['astro_pu_cost'], '695.4')
        self.assertEqual(rows[0]['astro_pu_items'], '1219.4')
        self.assertEqual(rows[0]['star_pu_oral_antibac_items'], '45.2')

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
        self.assertEqual(rows[1]['star_pu_oral_antibac_items'], '35.2')
        self.assertEqual(rows[1]['total_list_size'], '28')

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
        self.assertEqual(rows[0]['star_pu_oral_antibac_items'], '35.2')
        self.assertEqual(rows[0]['total_list_size'], '28')

    def test_api_view_org_details_all_practices(self):
        url = self.api_prefix
        url += '/org_details?format=csv&org_type=practice'
        response = self.client.get(url, follow=True)
        self.assertEqual(response.status_code, 200)
        reader = csv.DictReader(response.content.splitlines())
        rows = []
        for row in reader:
            rows.append(row)
        self.assertEqual(len(rows), 3)
        self.assertEqual(rows[0]['row_id'], 'N84014')
        self.assertEqual(rows[0]['row_name'], 'AINSDALE VILLAGE SURGERY')
        self.assertEqual(rows[0]['date'], '2015-01-01')
        self.assertEqual(rows[0]['total_list_size'], '25')
        self.assertEqual(rows[0]['astro_pu_cost'], '489.7')
        self.assertEqual(rows[0]['astro_pu_items'], '819.2')
        self.assertEqual(rows[0]['star_pu_oral_antibac_items'], '10.0')
        self.assertEqual(rows[2]['row_id'], 'P87629')
        self.assertEqual(rows[2]['date'], '2015-02-01')
        self.assertEqual(rows[2]['total_list_size'], '29')
        self.assertEqual(rows[2]['astro_pu_items'], '1600.2')
        self.assertEqual(rows[2]['star_pu_oral_antibac_items'], '29.0')

    def test_api_view_org_details_ccg_code_to_practices(self):
        url = self.api_prefix
        url += '/org_details?format=csv&org_type=practice&org=03Q'
        response = self.client.get(url, follow=True)
        self.assertEqual(response.status_code, 200)
        reader = csv.DictReader(response.content.splitlines())
        rows = []
        for row in reader:
            rows.append(row)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]['row_id'], 'N84014')
        self.assertEqual(rows[0]['row_name'], 'AINSDALE VILLAGE SURGERY')
        self.assertEqual(rows[0]['date'], '2015-01-01')
        self.assertEqual(rows[0]['total_list_size'], '25')
        self.assertEqual(rows[0]['astro_pu_cost'], '489.7')
        self.assertEqual(rows[0]['astro_pu_items'], '819.2')
        self.assertEqual(rows[0]['star_pu_oral_antibac_items'], '10.0')

    def test_api_view_org_details_one_practice(self):
        url = self.api_prefix
        url += '/org_details?format=csv&org_type=practice&org=N84014'
        response = self.client.get(url, follow=True)
        self.assertEqual(response.status_code, 200)
        reader = csv.DictReader(response.content.splitlines())
        rows = []
        for row in reader:
            rows.append(row)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]['row_id'], 'N84014')
        self.assertEqual(rows[0]['row_name'], 'AINSDALE VILLAGE SURGERY')
        self.assertEqual(rows[0]['date'], '2015-01-01')
        self.assertEqual(rows[0]['total_list_size'], '25')
        self.assertEqual(rows[0]['astro_pu_cost'], '489.7')
        self.assertEqual(rows[0]['astro_pu_items'], '819.2')
        self.assertEqual(rows[0]['star_pu_oral_antibac_items'], '10.0')
