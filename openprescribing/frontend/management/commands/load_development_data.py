from django.core.management import call_command
from django.core.management.base import BaseCommand

from frontend.tests.test_api_spending import TestAPISpendingViewsPPUTable


class Command(BaseCommand):

    help = 'Loads sample data intended for use in local development'

    def handle(self, *args, **options):
        # For now we just piggyback off the set of test fixtures used by the
        # API tests
        fixtures = TestAPISpendingViewsPPUTable.fixtures
        call_command('loaddata', *fixtures)
