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
    management.call_command('loaddata', fix_dir + 'prescriptions.json',
                            verbosity=0)
    management.call_command('loaddata', fix_dir + 'practice_listsizes.json',
                            verbosity=0)
    db_name = utils.get_env_setting('DB_NAME')
    db_user = utils.get_env_setting('DB_USER')
    db_pass = utils.get_env_setting('DB_PASS')
    management.call_command('create_matviews',
                            db_name='test_' + db_name,
                            db_user=db_user,
                            db_pass=db_pass)


def tearDownModule():
    args = []
    db_name = 'test_' + utils.get_env_setting('DB_NAME')
    db_user = utils.get_env_setting('DB_USER')
    db_pass = utils.get_env_setting('DB_PASS')
    opts = {
        'db_name': db_name,
        'db_user': db_user,
        'db_pass': db_pass
    }
    management.call_command('drop_matviews', *args, **opts)
    management.call_command('flush', verbosity=0, interactive=False)


class TestAPISpendingViews(TestCase):

    api_prefix = '/api/1.0'

    def test_codes_are_rejected_if_not_same_length(self):
        url = '%s/spending' % self.api_prefix
        url += '?format=csv&code=0202010B0,0202010B0AAAAAA'
        response = self.client.get(url, follow=True)
        self.assertEqual(response.status_code, 400)

    ########################################
    # Spending across all NHS England.
    ########################################
    def test_total_spending(self):
        url = '%s/spending?format=csv' % self.api_prefix
        response = self.client.get(url, follow=True)
        reader = csv.DictReader(response.content.splitlines())
        rows = []
        for row in reader:
            rows.append(row)
        self.assertEqual(len(rows), 6)
        self.assertEqual(rows[0]['date'], '2013-04-01')
        self.assertEqual(rows[0]['actual_cost'], '4.61')
        self.assertEqual(rows[0]['items'], '3')
        self.assertEqual(rows[5]['date'], '2014-11-01')
        self.assertEqual(rows[5]['actual_cost'], '90.54')
        self.assertEqual(rows[5]['items'], '95')

    def test_total_spending_by_bnf_section(self):
        url = '%s/spending?format=csv&code=2' % self.api_prefix
        response = self.client.get(url, follow=True)
        reader = csv.DictReader(response.content.splitlines())
        rows = []
        for row in reader:
            rows.append(row)
        self.assertEqual(len(rows), 6)
        self.assertEqual(rows[0]['date'], '2013-04-01')
        self.assertEqual(rows[0]['actual_cost'], '4.61')
        self.assertEqual(rows[0]['items'], '3')
        self.assertEqual(rows[5]['date'], '2014-11-01')
        self.assertEqual(rows[5]['actual_cost'], '90.54')
        self.assertEqual(rows[5]['items'], '95')

    def test_total_spending_by_bnf_section_full_code(self):
        url = '%s/spending?format=csv&code=02' % self.api_prefix
        response = self.client.get(url, follow=True)
        reader = csv.DictReader(response.content.splitlines())
        rows = []
        for row in reader:
            rows.append(row)
        self.assertEqual(len(rows), 6)
        self.assertEqual(rows[0]['date'], '2013-04-01')
        self.assertEqual(rows[0]['actual_cost'], '4.61')
        self.assertEqual(rows[0]['items'], '3')
        self.assertEqual(rows[5]['date'], '2014-11-01')
        self.assertEqual(rows[5]['actual_cost'], '90.54')
        self.assertEqual(rows[5]['items'], '95')

    def test_total_spending_by_code(self):
        url = '%s/spending?format=csv&code=0204000I0' % self.api_prefix
        response = self.client.get(url, follow=True)
        reader = csv.DictReader(response.content.splitlines())
        rows = []
        for row in reader:
            rows.append(row)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]['date'], '2014-11-01')
        self.assertEqual(rows[0]['actual_cost'], '36.28')
        self.assertEqual(rows[0]['items'], '33')

    def test_total_spending_by_codes(self):
        url = '%s/spending?format=csv' % self.api_prefix
        url += '&code=0204000I0,0202010F0'
        response = self.client.get(url, follow=True)
        reader = csv.DictReader(response.content.splitlines())
        rows = []
        for row in reader:
            rows.append(row)
        self.assertEqual(len(rows), 4)
        self.assertEqual(rows[2]['date'], '2014-09-01')
        self.assertEqual(rows[2]['actual_cost'], '13.98')
        self.assertEqual(rows[2]['items'], '2')

    ########################################
    # Total spending by CCG.
    ########################################
    def test_total_spending_by_ccg(self):
        url = '%s/spending_by_ccg?format=csv' % self.api_prefix
        response = self.client.get(url, follow=True)
        reader = csv.DictReader(response.content.splitlines())
        rows = []
        for row in reader:
            rows.append(row)
        self.assertEqual(len(rows), 9)
        self.assertEqual(rows[6]['row_id'], '03V')
        self.assertEqual(rows[6]['row_name'], 'NHS Corby')
        self.assertEqual(rows[6]['date'], '2014-09-01')
        self.assertEqual(rows[6]['actual_cost'], '38.28')
        self.assertEqual(rows[6]['items'], '41')

    def test_total_spending_by_one_ccg(self):
        url = '%s/spending_by_ccg?format=csv&org=03V' % self.api_prefix
        response = self.client.get(url, follow=True)
        reader = csv.DictReader(response.content.splitlines())
        rows = []
        for row in reader:
            rows.append(row)
        self.assertEqual(len(rows), 5)
        self.assertEqual(rows[-2]['row_id'], '03V')
        self.assertEqual(rows[-2]['row_name'], 'NHS Corby')
        self.assertEqual(rows[-2]['date'], '2014-09-01')
        self.assertEqual(rows[-2]['actual_cost'], '38.28')
        self.assertEqual(rows[-2]['items'], '41')

    def test_total_spending_by_multiple_ccgs(self):
        url = '%s/spending_by_ccg?format=csv&org=03V,03Q' % self.api_prefix
        response = self.client.get(url, follow=True)
        reader = csv.DictReader(response.content.splitlines())
        rows = []
        for row in reader:
            rows.append(row)
        self.assertEqual(len(rows), 9)
        self.assertEqual(rows[6]['row_id'], '03V')
        self.assertEqual(rows[6]['row_name'], 'NHS Corby')
        self.assertEqual(rows[6]['date'], '2014-09-01')
        self.assertEqual(rows[6]['actual_cost'], '38.28')
        self.assertEqual(rows[6]['items'], '41')

    def test_spending_by_all_ccgs_on_chemical(self):
        url = '%s/spending_by_ccg?format=csv&code=0202010B0' % self.api_prefix
        response = self.client.get(url, follow=True)
        reader = csv.DictReader(response.content.splitlines())
        rows = []
        for row in reader:
            rows.append(row)
        self.assertEqual(len(rows), 6)
        self.assertEqual(rows[0]['row_id'], '03V')
        self.assertEqual(rows[0]['row_name'], 'NHS Corby')
        self.assertEqual(rows[0]['date'], '2013-04-01')
        self.assertEqual(rows[0]['actual_cost'], '1.56')
        self.assertEqual(rows[0]['items'], '1')
        self.assertEqual(rows[5]['row_id'], '03V')
        self.assertEqual(rows[5]['row_name'], 'NHS Corby')
        self.assertEqual(rows[5]['date'], '2014-11-01')
        self.assertEqual(rows[5]['actual_cost'], '54.26')
        self.assertEqual(rows[5]['items'], '62')

    def test_spending_by_all_ccgs_on_multiple_chemicals(self):
        url = '%s/spending_by_ccg' % self.api_prefix
        url += '?format=csv&code=0202010B0,0202010F0'
        response = self.client.get(url, follow=True)
        reader = csv.DictReader(response.content.splitlines())
        rows = []
        for row in reader:
            rows.append(row)
        self.assertEqual(len(rows), 9)
        self.assertEqual(rows[0]['row_id'], '03Q')
        self.assertEqual(rows[0]['row_name'], 'NHS Vale of York')
        self.assertEqual(rows[0]['date'], '2013-04-01')
        self.assertEqual(rows[0]['actual_cost'], '3.05')
        self.assertEqual(rows[0]['items'], '2')
        self.assertEqual(rows[-3]['row_id'], '03V')
        self.assertEqual(rows[-3]['row_name'], 'NHS Corby')
        self.assertEqual(rows[-3]['date'], '2014-09-01')
        self.assertEqual(rows[-3]['actual_cost'], '38.28')
        self.assertEqual(rows[-3]['items'], '41')

    def test_spending_by_all_ccgs_on_product(self):
        url = '%s/spending_by_ccg' % self.api_prefix
        url += '?format=csv&code=0204000I0BC'
        response = self.client.get(url, follow=True)
        reader = csv.DictReader(response.content.splitlines())
        rows = []
        for row in reader:
            rows.append(row)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]['row_id'], '03V')
        self.assertEqual(rows[0]['row_name'], 'NHS Corby')
        self.assertEqual(rows[0]['date'], '2014-11-01')
        self.assertEqual(rows[0]['actual_cost'], '32.26')
        self.assertEqual(rows[0]['items'], '29')

    def test_spending_by_all_ccgs_on_presentation(self):
        url = '%s/spending_by_ccg' % self.api_prefix
        url += '?format=csv&code=0202010B0AAABAB'
        response = self.client.get(url, follow=True)
        reader = csv.DictReader(response.content.splitlines())
        rows = []
        for row in reader:
            rows.append(row)
        self.assertEqual(len(rows), 3)
        self.assertEqual(rows[2]['row_id'], '03V')
        self.assertEqual(rows[2]['row_name'], 'NHS Corby')
        self.assertEqual(rows[2]['date'], '2014-11-01')
        self.assertEqual(rows[2]['actual_cost'], '54.26')
        self.assertEqual(rows[2]['items'], '62')

    def test_spending_by_all_ccgs_on_multiple_presentations(self):
        url = '%s/spending_by_ccg' % self.api_prefix
        url += '?format=csv&code=0202010F0AAAAAA,0202010B0AAACAC'
        response = self.client.get(url, follow=True)
        reader = csv.DictReader(response.content.splitlines())
        rows = []
        for row in reader:
            rows.append(row)
        self.assertEqual(len(rows), 7)
        self.assertEqual(rows[0]['row_id'], '03Q')
        self.assertEqual(rows[0]['row_name'], 'NHS Vale of York')
        self.assertEqual(rows[0]['date'], '2013-04-01')
        self.assertEqual(rows[0]['actual_cost'], '3.05')
        self.assertEqual(rows[0]['items'], '2')

    def test_spending_by_all_ccgs_on_bnf_section(self):
        url = '%s/spending_by_ccg?format=csv&code=2.2.1' % self.api_prefix
        response = self.client.get(url, follow=True)
        reader = csv.DictReader(response.content.splitlines())
        rows = []
        for row in reader:
            rows.append(row)
        self.assertEqual(len(rows), 9)
        self.assertEqual(rows[0]['row_id'], '03Q')
        self.assertEqual(rows[0]['row_name'], 'NHS Vale of York')
        self.assertEqual(rows[0]['date'], '2013-04-01')
        self.assertEqual(rows[0]['actual_cost'], '3.05')
        self.assertEqual(rows[0]['items'], '2')
        self.assertEqual(rows[-1]['row_id'], '03V')
        self.assertEqual(rows[-1]['row_name'], 'NHS Corby')
        self.assertEqual(rows[-1]['date'], '2014-11-01')
        self.assertEqual(rows[-1]['actual_cost'], '54.26')
        self.assertEqual(rows[-1]['items'], '62')

    def test_spending_by_all_ccgs_on_multiple_bnf_sections(self):
        url = '%s/spending_by_ccg?format=csv&code=2.2,2.4' % self.api_prefix
        response = self.client.get(url, follow=True)
        reader = csv.DictReader(response.content.splitlines())
        rows = []
        for row in reader:
            rows.append(row)
        self.assertEqual(len(rows), 9)
        self.assertEqual(rows[-1]['row_id'], '03V')
        self.assertEqual(rows[-1]['row_name'], 'NHS Corby')
        self.assertEqual(rows[-1]['date'], '2014-11-01')
        self.assertEqual(rows[-1]['actual_cost'], '90.54')
        self.assertEqual(rows[-1]['items'], '95')

    ########################################
    # Total spending by practice.
    ########################################
    def test_spending_by_all_practices_on_product_without_date(self):
        url = '%s/spending_by_practice' % self.api_prefix
        url += '?format=csv&code=0204000I0BC'
        response = self.client.get(url, follow=True)
        self.assertEqual(response.status_code, 400)

    def test_total_spending_by_practice(self):
        url = '%s/spending_by_practice' % self.api_prefix
        url += '?format=csv&date=2014-11-01'
        response = self.client.get(url, follow=True)
        reader = csv.DictReader(response.content.splitlines())
        rows = []
        for row in reader:
            rows.append(row)
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]['row_id'], 'K83059')
        self.assertEqual(rows[0]['row_name'], 'DR KHALID & PARTNERS')
        self.assertEqual(rows[0]['date'], '2014-11-01')
        self.assertEqual(rows[0]['setting'], '-1')
        self.assertEqual(rows[0]['ccg'], '03V')
        self.assertEqual(rows[0]['actual_cost'], '26.28')
        self.assertEqual(rows[0]['items'], '40')

    def test_spending_by_practice_on_chemical(self):
        url = '%s/spending_by_practice' % self.api_prefix
        url += '?format=csv&code=0204000I0&date=2014-11-01'
        response = self.client.get(url, follow=True)
        reader = csv.DictReader(response.content.splitlines())
        rows = []
        for row in reader:
            rows.append(row)
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]['row_id'], 'K83059')
        self.assertEqual(rows[0]['row_name'], 'DR KHALID & PARTNERS')
        self.assertEqual(rows[0]['setting'], '-1')
        self.assertEqual(rows[0]['ccg'], '03V')
        self.assertEqual(rows[0]['date'], '2014-11-01')
        self.assertEqual(rows[0]['actual_cost'], '14.15')
        self.assertEqual(rows[0]['items'], '16')

    def test_spending_by_all_practices_on_chemical_with_date(self):
        url = '%s/spending_by_practice' % self.api_prefix
        url += '?format=csv&code=0202010F0&date=2014-09-01'
        response = self.client.get(url, follow=True)
        reader = csv.DictReader(response.content.splitlines())
        rows = []
        for row in reader:
            rows.append(row)
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]['row_id'], 'N84014')
        self.assertEqual(rows[0]['actual_cost'], '11.99')
        self.assertEqual(rows[0]['items'], '1')
        self.assertEqual(rows[1]['row_id'], 'P87629')
        self.assertEqual(rows[1]['actual_cost'], '1.99')
        self.assertEqual(rows[1]['items'], '1')

    def test_spending_by_one_practice(self):
        url = '%s/spending_by_practice?format=csv&org=P87629' % self.api_prefix
        response = self.client.get(url, follow=True)
        reader = csv.DictReader(response.content.splitlines())
        rows = []
        for row in reader:
            rows.append(row)
        self.assertEqual(len(rows), 5)
        self.assertEqual(rows[-1]['row_id'], 'P87629')
        self.assertEqual(rows[-1]['row_name'], '1/ST ANDREWS MEDICAL PRACTICE')
        self.assertEqual(rows[-1]['date'], '2014-11-01')
        self.assertEqual(rows[-1]['actual_cost'], '64.26')
        self.assertEqual(rows[-1]['items'], '55')

    def test_spending_by_one_practice_on_chemical(self):
        url = '%s/spending_by_practice' % self.api_prefix
        url += '?format=csv&code=0202010B0&org=P87629'
        response = self.client.get(url, follow=True)
        reader = csv.DictReader(response.content.splitlines())
        rows = []
        for row in reader:
            rows.append(row)
        self.assertEqual(len(rows), 5)
        self.assertEqual(rows[-1]['row_id'], 'P87629')
        self.assertEqual(rows[-1]['row_name'], '1/ST ANDREWS MEDICAL PRACTICE')
        self.assertEqual(rows[-1]['setting'], '4')
        self.assertEqual(rows[-1]['ccg'], '03V')
        self.assertEqual(rows[-1]['date'], '2014-11-01')
        self.assertEqual(rows[-1]['actual_cost'], '42.13')
        self.assertEqual(rows[-1]['items'], '38')

    def test_spending_by_practice_on_multiple_chemicals(self):
        url = self.api_prefix
        url += '/spending_by_practice?format=csv'
        url += '&code=0202010B0,0204000I0&org=P87629,K83059'
        response = self.client.get(url, follow=True)
        reader = csv.DictReader(response.content.splitlines())
        rows = []
        for row in reader:
            rows.append(row)
        self.assertEqual(len(rows), 6)
        self.assertEqual(rows[2]['row_id'], 'P87629')
        self.assertEqual(rows[2]['row_name'], '1/ST ANDREWS MEDICAL PRACTICE')
        self.assertEqual(rows[2]['date'], '2013-10-01')
        self.assertEqual(rows[2]['actual_cost'], '1.62')
        self.assertEqual(rows[2]['items'], '1')

    def test_spending_by_all_practices_on_product(self):
        url = '%s/spending_by_practice' % self.api_prefix
        url += '?format=csv&code=0202010B0AA&date=2014-11-01'
        response = self.client.get(url, follow=True)
        reader = csv.DictReader(response.content.splitlines())
        rows = []
        for row in reader:
            rows.append(row)
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]['row_id'], 'K83059')
        self.assertEqual(rows[0]['actual_cost'], '12.13')
        self.assertEqual(rows[0]['items'], '24')
        self.assertEqual(rows[1]['row_id'], 'P87629')
        self.assertEqual(rows[1]['actual_cost'], '42.13')
        self.assertEqual(rows[1]['items'], '38')

    def test_spending_by_all_practices_on_presentation(self):
        url = '%s/spending_by_practice' % self.api_prefix
        url += '?format=csv&code=0202010B0AAABAB&date=2014-11-01'
        response = self.client.get(url, follow=True)
        reader = csv.DictReader(response.content.splitlines())
        rows = []
        for row in reader:
            rows.append(row)
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]['row_id'], 'K83059')
        self.assertEqual(rows[0]['actual_cost'], '12.13')
        self.assertEqual(rows[0]['items'], '24')
        self.assertEqual(rows[1]['row_id'], 'P87629')
        self.assertEqual(rows[1]['actual_cost'], '42.13')
        self.assertEqual(rows[1]['items'], '38')

    def test_spending_by_practice_on_presentation(self):
        url = '%s/spending_by_practice' % self.api_prefix
        url += '?format=csv&code=0204000I0BCAAAB&org=03V'
        response = self.client.get(url, follow=True)
        reader = csv.DictReader(response.content.splitlines())
        rows = []
        for row in reader:
            rows.append(row)
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[1]['row_id'], 'P87629')
        self.assertEqual(rows[1]['row_name'], '1/ST ANDREWS MEDICAL PRACTICE')
        self.assertEqual(rows[1]['setting'], '4')
        self.assertEqual(rows[1]['ccg'], '03V')
        self.assertEqual(rows[1]['date'], '2014-11-01')
        self.assertEqual(rows[1]['actual_cost'], '22.13')
        self.assertEqual(rows[1]['items'], '17')

    def test_spending_by_practice_on_multiple_presentations(self):
        url = self.api_prefix
        url += '/spending_by_practice'
        url += '?format=csv&code=0204000I0BCAAAB,0202010B0AAABAB&org=03V'
        response = self.client.get(url, follow=True)
        reader = csv.DictReader(response.content.splitlines())
        rows = []
        for row in reader:
            rows.append(row)
        self.assertEqual(len(rows), 3)
        self.assertEqual(rows[2]['row_id'], 'P87629')
        self.assertEqual(rows[2]['row_name'], '1/ST ANDREWS MEDICAL PRACTICE')
        self.assertEqual(rows[2]['date'], '2014-11-01')
        self.assertEqual(rows[2]['actual_cost'], '64.26')
        self.assertEqual(rows[2]['items'], '55')

    def test_spending_by_practice_on_section(self):
        url = '%s/spending_by_practice' % self.api_prefix
        url += '?format=csv&code=2&org=03V'
        response = self.client.get(url, follow=True)
        reader = csv.DictReader(response.content.splitlines())
        rows = []
        for row in reader:
            rows.append(row)
        self.assertEqual(len(rows), 6)
        self.assertEqual(rows[-1]['row_id'], 'P87629')
        self.assertEqual(rows[-1]['row_name'], '1/ST ANDREWS MEDICAL PRACTICE')
        self.assertEqual(rows[-1]['date'], '2014-11-01')
        self.assertEqual(rows[-1]['actual_cost'], '64.26')
        self.assertEqual(rows[-1]['items'], '55')

    def test_spending_by_practice_on_multiple_sections(self):
        url = '%s/spending_by_practice' % self.api_prefix
        url += '?format=csv&code=0202,0204&org=03Q'
        response = self.client.get(url, follow=True)
        reader = csv.DictReader(response.content.splitlines())
        rows = []
        for row in reader:
            rows.append(row)
        self.assertEqual(len(rows), 4)
        self.assertEqual(rows[0]['row_id'], 'N84014')
        self.assertEqual(rows[0]['row_name'], 'AINSDALE VILLAGE SURGERY')
        self.assertEqual(rows[0]['date'], '2013-04-01')
        self.assertEqual(rows[0]['actual_cost'], '3.05')
        self.assertEqual(rows[0]['items'], '2')
