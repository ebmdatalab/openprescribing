import csv

from django.db import connection
from django.http import Http404
from django.test import TransactionTestCase

import api.view_utils

class ApiTestBase(TransactionTestCase):
    """Base test case that sets up all the fixtures required by any of the
    API tests.

    """
    fixtures = ['ccgs', 'practices', 'practice_listsizes', 'products',
                'presentations', 'sections', 'prescriptions',
                'chemicals', 'tariff']
    api_prefix = '/api/1.0'

    @classmethod
    def setUpClass(cls):
        super(ApiTestBase, cls).setUpClass()
        api.view_utils.DISABLE_DB_TIMEOUT = True

    @classmethod
    def tearDownClass(cls):
        api.view_utils.DISABLE_DB_TIMEOUT = False
        super(ApiTestBase, cls).tearDownClass()

    def setUp(self):
        view_create = 'frontend/management/commands/replace_matviews.sql'
        fixture = 'frontend/tests/fixtures/api_test_data.sql'
        with connection.cursor() as cursor:
            with open(view_create, 'r') as f:
                # Creates the view tables
                cursor.execute(f.read())
            with open(fixture, 'r') as f:
                # Fills them with test data
                cursor.execute(f.read())
        super(ApiTestBase, self).setUp()

    def _rows_from_api(self, url):
        url = self.api_prefix + url
        response = self.client.get(url, follow=True)
        if response.status_code == 404:
            raise Http404("URL %s does not exist" % url)
        reader = csv.DictReader(response.content.splitlines())
        rows = []
        for row in reader:
            rows.append(row)
        return rows
