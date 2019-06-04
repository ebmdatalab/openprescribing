from django.core.management import call_command
from django.core.management.base import BaseCommand

from frontend.models import ImportLog, PPUSaving
from frontend.tests.test_api_spending import ApiTestBase, TestAPISpendingViewsPPUTable


class Command(BaseCommand):

    help = 'Loads sample data intended for use in local development'

    def handle(self, *args, **options):
        # For now we just piggyback off the set of test fixtures used by the
        # API tests
        fixtures = TestAPISpendingViewsPPUTable.fixtures
        call_command('loaddata', *fixtures)
        ApiTestBase.setUpTestData()
        max_ppu_date = PPUSaving.objects.order_by('-date')[0].date
        ImportLog.objects.create(current_at=max_ppu_date, category='ppu')
