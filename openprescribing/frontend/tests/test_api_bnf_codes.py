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
    management.call_command('loaddata', fix_dir + 'products.json',
                            verbosity=0)
    management.call_command('loaddata', fix_dir + 'sections.json',
                            verbosity=0)
    management.call_command('loaddata', fix_dir + 'presentations.json',
                            verbosity=0)
    management.call_command('loaddata', fix_dir + 'ccgs.json',
                            verbosity=0)
    management.call_command('loaddata', fix_dir + 'practices.json',
                            verbosity=0)
    management.call_command('loaddata', fix_dir + 'shas.json',
                            verbosity=0)
    management.call_command('loaddata', fix_dir + 'prescriptions.json',
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


class TestAPIBNFCodeViews(TestCase):

    api_prefix = '/api/1.0'

    def test_api_view_bnf_chemical(self):
        url = '%s/bnf_code?q=lor&format=json' % self.api_prefix
        response = self.client.get(url, follow=True)
        self.assertEqual(response.status_code, 200)
        content = json.loads(response.content)
        self.assertEqual(len(content), 5)
        self.assertEqual(content[0]['id'], '0202010D0')
        self.assertEqual(content[0]['name'], 'Chlorothiazide')
        self.assertEqual(content[0]['type'], 'chemical')
        self.assertEqual(content[3]['id'], '0202010D0AA')
        self.assertEqual(content[3]['name'], 'Chloroth')
        self.assertEqual(content[3]['type'], 'product')

        url = '%s/bnf_code?q=0202&format=json' % self.api_prefix
        response = self.client.get(url, follow=True)
        self.assertEqual(response.status_code, 200)
        content = json.loads(response.content)
        self.assertEqual(len(content), 9)
        self.assertEqual(content[0]['id'], '0202010B0')
        self.assertEqual(content[0]['name'], 'Bendroflumethiazide')
        self.assertEqual(content[0]['section'], '2.2: Diuretics')

        url = '%s/bnf_code?q=0202&exact=true&format=json' % self.api_prefix
        response = self.client.get(url, follow=True)
        self.assertEqual(response.status_code, 200)
        content = json.loads(response.content)
        self.assertEqual(len(content), 0)

        url = '%s/bnf_code?q=0202010D0BD&exact=true&format=json' % self.api_prefix
        response = self.client.get(url, follow=True)
        self.assertEqual(response.status_code, 200)
        content = json.loads(response.content)
        self.assertEqual(len(content), 1)
        self.assertEqual(content[0]['id'], '0202010D0BD')
        self.assertEqual(content[0]['name'], 'Chlotride')
        self.assertEqual(content[0]['is_generic'], False)

    def test_api_view_bnf_section(self):
        url = '%s/bnf_code?q=diuretics&format=json' % self.api_prefix
        response = self.client.get(url, follow=True)
        self.assertEqual(response.status_code, 200)
        content = json.loads(response.content)
        self.assertEqual(len(content), 2)
        self.assertEqual(content[0]['id'], '2.2')
        self.assertEqual(content[0]['name'], 'Diuretics')
        self.assertEqual(content[0]['type'], 'BNF section')
        self.assertEqual(content[1]['id'], '2.2.1')
        self.assertEqual(content[1]['name'], 'Thiazides And Related Diuretics')
        self.assertEqual(content[1]['type'], 'BNF paragraph')

        url = '%s/bnf_code?q=cardio&format=json' % self.api_prefix
        response = self.client.get(url, follow=True)
        self.assertEqual(response.status_code, 200)
        content = json.loads(response.content)
        self.assertEqual(len(content), 1)
        self.assertEqual(content[0]['id'], '2')
        self.assertEqual(content[0]['name'], 'Cardiovascular System')
        self.assertEqual(content[0]['type'], 'BNF chapter')

        url = '%s/bnf_code?q=2.2&exact=true&format=json' % self.api_prefix
        response = self.client.get(url, follow=True)
        self.assertEqual(response.status_code, 200)
        content = json.loads(response.content)
        self.assertEqual(len(content), 1)
        self.assertEqual(content[0]['id'], '2.2')
        self.assertEqual(content[0]['name'], 'Diuretics')
        self.assertEqual(content[0]['type'], 'BNF section')

    def test_api_view_bnf_presentation(self):
        url = '%s/bnf_code?q=Bendroflume&format=json' % self.api_prefix
        response = self.client.get(url, follow=True)
        self.assertEqual(response.status_code, 200)
        content = json.loads(response.content)
        self.assertEqual(len(content), 3)
        self.assertEqual(content[0]['id'], '0202010B0')
        self.assertEqual(content[0]['name'], 'Bendroflumethiazide')

        url = '%s/bnf_code?q=0202010F0AAAAAA&format=json' % self.api_prefix
        response = self.client.get(url, follow=True)
        self.assertEqual(response.status_code, 200)
        content = json.loads(response.content)
        self.assertEqual(len(content), 1)
        self.assertEqual(content[0]['id'], '0202010F0AAAAAA')
        self.assertEqual(content[0]['name'], 'Chlortalidone_Tab 50mg')
        self.assertEqual(content[0]['type'], 'product format')

        url = '%s/bnf_code?q=0202010F0AAA&exact=true&format=json' % self.api_prefix
        response = self.client.get(url, follow=True)
        self.assertEqual(response.status_code, 200)
        content = json.loads(response.content)
        self.assertEqual(len(content), 0)
