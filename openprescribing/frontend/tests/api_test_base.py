from django.db import connection
from django.test import TestCase


class ApiTestBase(TestCase):
    """Base test case that sets up all the fixtures required by any of the
    API tests.

    """
    fixtures = ['ccgs', 'practices', 'practice_listsizes', 'products',
                'presentations', 'sections', 'prescriptions', 'chemicals']
    api_prefix = '/api/1.0'

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
