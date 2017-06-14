from datetime import date

from ebmdatalab import bigquery

from django.conf import settings
from django.core.management import call_command
from django.test import TestCase

from frontend.management.commands import import_ppu_savings
from frontend.models import PPUSaving


class BigqueryFunctionalTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        fixtures_base = 'frontend/tests/fixtures/commands/'
        prescribing_fixture = (fixtures_base +
                               'prescribing_bigquery_fixture.csv')
        bigquery.load_prescribing_data_from_file(
            'hscic',
            settings.BQ_PRESCRIBING_TABLE_NAME + '_legacy',
            prescribing_fixture)
        month = date(2015, 9, 1)
        import_ppu_savings.Command().handle(
            month=month,
            substitutions_csv=fixtures_base + 'ppu_substitutions.csv',
            min_ccg_saving=0,
            min_practice_saving=0,
            limit=1
        )

    def test_savings_created_correctly(self):
        ccg_saving = PPUSaving.objects.get(practice_id__isnull=True)
        practice_saving = PPUSaving.objects.get(practice_id__isnull=False)
        for saving in [ccg_saving, practice_saving]:
            # There's only one saving, so they should be identical
            # apart from the practice_id
            self.assertEqual(saving.lowest_decile, 10.0)
            self.assertEqual(saving.pct_id, '02Q')
            self.assertEqual(saving.formulation_swap, 'Tab / Cap')
            self.assertEqual(saving.price_per_unit, 10050.0)
            self.assertEqual(saving.presentation_id, '0408010A0AAAAAA')
            self.assertEqual(saving.possible_savings, 100400.0)
            self.assertEqual(saving.date, date(2015, 9, 1))
            self.assertEqual(saving.quantity, 10)
