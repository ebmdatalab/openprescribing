from datetime import date
import os

from gcutils.bigquery import Client

from django.conf import settings
from django.test import TestCase
import pandas as pd
from mock import patch

from frontend import bq_schemas
from frontend.management.commands import import_ppu_savings
from frontend.models import PPUSaving


class BigqueryFunctionalTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        fixtures_base_path = os.path.join(
            'frontend', 'tests', 'fixtures', 'commands',
        )

        client = Client('hscic')

        prescribing_fixture_path = os.path.join(
            fixtures_base_path,
            'prescribing_bigquery_fixture.csv'
        )
        table = client.get_or_create_table(
            'normalised_prescribing_standard',
            bq_schemas.PRESCRIBING_SCHEMA
        )
        table.insert_rows_from_csv(prescribing_fixture_path)

        practices_fixture_path = os.path.join(
            fixtures_base_path,
            'practices.csv'
        )
        table = client.get_or_create_table(
            'practices',
            bq_schemas.PRACTICE_SCHEMA
        )
        columns = [field.name for field in bq_schemas.PRACTICE_SCHEMA]
        table.insert_rows_from_csv(practices_fixture_path)

        tariff_path = os.path.join(fixtures_base_path, 'tariff_fixture.csv')
        table = client.get_or_create_table('tariff', bq_schemas.TARIFF_SCHEMA)
        table.insert_rows_from_csv(tariff_path)

        bnf_path = os.path.join(
            fixtures_base_path,
            'bnf_codes_for_ppu_savings.csv'
        )
        table = client.get_or_create_table('bnf', bq_schemas.BNF_SCHEMA)
        table.insert_rows_from_csv(bnf_path)

        month = date(2015, 9, 1)
        dummy_substitutions = pd.read_csv(
            os.path.join(fixtures_base_path, 'ppu_substitutions.csv'))
        with patch(
                'frontend.management.commands.import_ppu_savings.pd.read_csv',
                return_value=dummy_substitutions):
            import_ppu_savings.Command().handle(month=month)

    def test_savings_created_correctly(self):
        ccg_saving = PPUSaving.objects.get(
            presentation_id='0408010A0AAAAAA',
            pct_id='02Q',
            practice_id__isnull=True
        )
        practice_saving = PPUSaving.objects.get(
            presentation_id='0408010A0AAAAAA',
            pct_id='02Q',
            practice_id__isnull=False
        )
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
