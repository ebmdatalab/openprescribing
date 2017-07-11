import datetime
import os
import json
import unittest
from django.core import management
from django.test import TestCase

from frontend.models import PCT


def setUpModule():
    fix_dir = 'frontend/tests/fixtures/'
    management.call_command('loaddata', fix_dir + 'ccgs.json',
                            verbosity=0)
    management.call_command('loaddata', fix_dir + 'practices.json',
                            verbosity=0)


def tearDownModule():
    management.call_command('flush', verbosity=0, interactive=False)


class TestAPIOrgLocationViews(TestCase):

    api_prefix = '/api/1.0'

    def test_api_view_org_location_all_ccgs(self):
        url = '%s/org_location?org_type=ccg&format=json' % self.api_prefix
        response = self.client.get(url, follow=True)
        self.assertEqual(response.status_code, 200)
        content = json.loads(response.content)
        self.assertEqual(len(content['features']), 2)
        coord = content['features'][1]['geometry']['coordinates'][0][0][0]
        self.assertEqual(coord[0], -117.00000000000003)
        self.assertEqual(coord[1], 33.97943076318428)

    def test_api_view_org_location_all_ccgs_excluding_closed(self):
        closed = PCT.objects.first()
        closed.close_date = datetime.date(2001, 1, 1)
        closed.save()
        url = '%s/org_location?org_type=ccg&format=json' % self.api_prefix
        response = self.client.get(url, follow=True)
        self.assertEqual(response.status_code, 200)
        content = json.loads(response.content)
        self.assertEqual(len(content['features']), 1)

    def test_api_view_org_location_ccg_by_code(self):
        url = ('%s/org_location?org_type=ccg&q=03Q,03V&format=json' %
               self.api_prefix)
        response = self.client.get(url, follow=True)
        self.assertEqual(response.status_code, 200)
        content = json.loads(response.content)
        self.assertEqual(len(content['features']), 2)
        coord = content['features'][0]['geometry']['coordinates'][0][0][0]
        self.assertEqual(coord[0], -117.00000000000003)
        self.assertEqual(coord[1], 33.97943076318428)

    @unittest.skipIf("TRAVIS" in os.environ and os.environ["TRAVIS"],
                     "Skipping this test on Travis CI.")
    def test_api_view_org_location_practice_by_code(self):
        url = ('%s/org_location?org_type=practice&q=03Q&format=json'
               % self.api_prefix)
        response = self.client.get(url, follow=True)
        self.assertEqual(response.status_code, 200)
        content = json.loads(response.content)
        self.assertEqual(len(content['features']), 1)
        props = content['features'][0]['properties']
        self.assertEqual(props['name'], 'AINSDALE VILLAGE SURGERY')
        self.assertEqual(props['setting'], 4)
        coord = content['features'][0]['geometry']['coordinates']
        self.assertEqual(coord[0], 1.0)
        self.assertEqual(coord[1], 51.5)
