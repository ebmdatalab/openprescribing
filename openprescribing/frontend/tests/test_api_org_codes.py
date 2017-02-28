import csv
import os
import json
import unittest
from django.core import management
from django.test import TestCase
from common import utils


def setUpModule():
    fix_dir = 'frontend/tests/fixtures/'
    management.call_command('loaddata', fix_dir + 'ccgs.json',
                            verbosity=0)
    management.call_command('loaddata', fix_dir + 'practices.json',
                            verbosity=0)


def tearDownModule():
    management.call_command('flush', verbosity=0, interactive=False)


class TestAPIOrgViews(TestCase):

    api_prefix = '/api/1.0'

    def test_api_view_org_code(self):
        url = '%s/org_code?q=ainsdale&format=json' % self.api_prefix
        response = self.client.get(url, follow=True)
        self.assertEqual(response.status_code, 200)
        content = json.loads(response.content)
        self.assertEqual(len(content), 1)
        self.assertEqual(content[0]['code'], 'N84014')
        self.assertEqual(content[0]['name'], 'AINSDALE VILLAGE SURGERY')

        url = '%s/org_code?q=P87&format=json' % self.api_prefix
        response = self.client.get(url, follow=True)
        self.assertEqual(response.status_code, 200)
        content = json.loads(response.content)
        self.assertEqual(len(content), 1)
        self.assertEqual(content[0]['code'], 'P87629')
        self.assertEqual(content[0]['name'], '1/ST ANDREWS MEDICAL PRACTICE')
        self.assertEqual(content[0]['type'], 'Practice')
        self.assertEqual(content[0]['setting'], 4)
        self.assertEqual(content[0]['setting_name'], 'GP Practice')

        url = '%s/org_code?q=03&format=json' % self.api_prefix
        response = self.client.get(url, follow=True)
        self.assertEqual(response.status_code, 200)
        content = json.loads(response.content)
        self.assertEqual(len(content), 2)
        self.assertEqual(content[0]['code'], '03Q')
        self.assertEqual(content[0]['name'], 'NHS Vale of York')

    def test_api_view_org_code_org_type(self):
        url = '%s/org_code?q=a&org_type=practice&format=json' % self.api_prefix
        response = self.client.get(url, follow=True)
        self.assertEqual(response.status_code, 200)
        content = json.loads(response.content)
        self.assertEqual(len(content), 3)
        self.assertEqual(content[0]['code'], 'P87629')
        self.assertEqual(content[0]['name'], '1/ST ANDREWS MEDICAL PRACTICE')

        url = '%s/org_code?q=a&org_type=CCG&format=json' % self.api_prefix
        response = self.client.get(url, follow=True)
        self.assertEqual(response.status_code, 200)
        content = json.loads(response.content)
        self.assertEqual(len(content), 1)
        self.assertEqual(content[0]['code'], '03Q')
        self.assertEqual(content[0]['name'], 'NHS Vale of York')

        url = '%s/org_code?q=Mer&org_type=AT&format=json' % self.api_prefix
        response = self.client.get(url, follow=True)
        self.assertEqual(response.status_code, 200)
        content = json.loads(response.content)
        self.assertEqual(len(content), 1)
        self.assertEqual(content[0]['code'], 'Q48')
        self.assertEqual(content[0]['name'], 'Merseyside')

        url = '%s/org_code?q=a&org_type=CCG,AT&format=json' % self.api_prefix
        response = self.client.get(url, follow=True)
        self.assertEqual(response.status_code, 200)
        content = json.loads(response.content)
        self.assertEqual(len(content), 2)
        self.assertEqual(content[0]['code'], '03Q')
        self.assertEqual(content[0]['name'], 'NHS Vale of York')
        self.assertEqual(content[0]['type'], 'CCG')
        self.assertEqual(content[1]['code'], 'Q46')
        self.assertEqual(content[1]['name'], 'Greater Manchester')
        self.assertEqual(content[1]['type'], 'Area Team')

    def test_api_view_org_code_is_exact(self):
        url = '%s/org_code?q=N84014&exact=true&format=json' % self.api_prefix
        response = self.client.get(url, follow=True)
        self.assertEqual(response.status_code, 200)
        content = json.loads(response.content)
        self.assertEqual(len(content), 1)
        self.assertEqual(content[0]['code'], 'N84014')
        self.assertEqual(content[0]['name'], 'AINSDALE VILLAGE SURGERY')

        url = '%s/org_code?q=P87&exact=true&format=json' % self.api_prefix
        response = self.client.get(url, follow=True)
        self.assertEqual(response.status_code, 200)
        content = json.loads(response.content)
        self.assertEqual(len(content), 0)

    def test_api_view_all_orgs(self):
        url = '%s/org_code?format=json' % self.api_prefix
        response = self.client.get(url, follow=True)
        self.assertEqual(response.status_code, 200)
        content = json.loads(response.content)
        self.assertEqual(len(content), 7)
        self.assertEqual(content[0]['code'], 'Q48')
        self.assertEqual(content[0]['name'], 'Merseyside')
        self.assertEqual(content[0]['type'], 'Area Team')
        self.assertEqual(content[2]['code'], '03Q')
        self.assertEqual(content[2]['name'], 'NHS Vale of York')
        self.assertEqual(content[2]['type'], 'CCG')
        self.assertEqual(content[-1]['code'], 'K83059')
        self.assertEqual(content[-1]['name'], 'DR KHALID & PARTNERS')
        self.assertEqual(content[-1]['type'], 'Practice')
