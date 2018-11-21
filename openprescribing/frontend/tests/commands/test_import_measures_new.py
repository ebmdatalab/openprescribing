from __future__ import print_function

import csv
import tempfile
from random import randint

import pandas as pd

from django.core.management import call_command
from django.test import TestCase

from frontend import bq_schemas as schemas
from frontend.models import ImportLog, MeasureGlobal, MeasureValue, Practice, PCT, STP, RegionalTeam
from gcutils.bigquery import Client


class ImportMeasuresTests(TestCase):
    def test_import_measures(self):
        # This test verifies the behaviour of import_measures by repeating the
        # measure calculations with Pandas, and asserting that the values
        # stored on MeasureValue and MeasureGlobal objects match those
        # calculated with Pandas.  See notebooks/measure-calculations.ipynb for
        # an explanation of these calculations.

        # Create a bunch of RegionalTeams, STPs, CCGs, Practices
        for regtm_ix in range(5):
            regtm = RegionalTeam.objects.create(
                code='Y0{}'.format(regtm_ix),
                name='Region {}'.format(regtm_ix),
            )

            for stp_ix in range(5):
                stp = STP.objects.create(
                    ons_code='E000000{}{}'.format(regtm_ix, stp_ix),
                    name='STP {}'.format(regtm_ix, stp_ix),
                )

                for ccg_ix in range(5):
                    ccg = PCT.objects.create(
                        regional_team=regtm,
                        stp=stp,
                        code='{}{}{}'.format(regtm_ix, stp_ix, ccg_ix).replace('0', 'A'),
                        name='CCG {}/{}/{}'.format(regtm_ix, stp_ix, ccg_ix),
                        org_type='CCG',
                    )

                    for prac_ix in range(5):
                        Practice.objects.create(
                            ccg=ccg,
                            code='P0{}{}{}{}'.format(regtm_ix, stp_ix, ccg_ix, prac_ix),
                            name='Practice {}/{}/{}/{}'.format(regtm_ix, stp_ix, ccg_ix, prac_ix),
                            setting=4,
                        )

        # import_measures uses this ImportLog to work out which months it
        # should import data.
        ImportLog.objects.create(
            category='prescribing',
            current_at='2018-08-01',
        )

        # Set up BQ, and upload STPs, CCGs, Practices.
        Client('measures').create_dataset()
        client = Client('hscic')
        table = client.get_or_create_table('ccgs', schemas.CCG_SCHEMA)
        columns = [field.name for field in schemas.CCG_SCHEMA]
        table.insert_rows_from_pg(PCT, columns, schemas.ccgs_transform)
        table = client.get_or_create_table('practices', schemas.PRACTICE_SCHEMA)
        columns = [field.name for field in schemas.PRACTICE_SCHEMA]
        table.insert_rows_from_pg(Practice, columns)

        # Generate random prescribing data.  This data is never saved to the
        # database.
        presentations = [
            ('0703021Q0AAAAAA', 'Desogestrel_Tab 75mcg'),        # generic
            ('0703021Q0BBAAAA', 'Cerazette_Tab 75mcg'),          # branded
            ('076543210AAAAAA', 'Etynodiol Diacet_Tab 500mcg'),  # irrelevant
        ]

        prescribing_rows = []
        seen_practice_with_no_prescribing = False
        seen_practice_with_no_relevant_prescribing = False
        seen_practice_with_no_generic_prescribing = False
        seen_practice_with_no_branded_prescribing = False

        for practice in Practice.objects.all():
            for month in [7, 8]:
                timestamp = '2018-0{}-01 00:00:00 UTC'.format(month)

                for ix, (bnf_code, bnf_name) in enumerate(presentations):
                    if practice.code == 'P00000':
                        seen_practice_with_no_prescribing = True
                        continue
                    elif practice.code == 'P00010' and '0703021Q' in bnf_code:
                        seen_practice_with_no_relevant_prescribing = True
                        continue
                    elif practice.code == 'P00020' and bnf_code == '0703021Q0AAAAAA':
                        seen_practice_with_no_generic_prescribing = True
                        continue
                    elif practice.code == 'P00030' and bnf_code == '0703021Q0BBAAAA':
                        seen_practice_with_no_branded_prescribing = True
                        continue

                    items = randint(0, 100)
                    quantity = randint(6, 28) * items

                    # Multiplying by (1 + ix) ensures that the branded cost is
                    # always higher than the generic cost.
                    actual_cost =  (1 + ix) * randint(100, 200) * quantity * 0.01

                    # We don't care about net_cost.
                    net_cost = actual_cost

                    row = [
                        'sha',  #  This value doesn't matter.
                        practice.ccg.regional_team_id,
                        practice.ccg.stp_id,
                        practice.ccg_id,
                        practice.code,
                        bnf_code,
                        bnf_name,
                        items,
                        net_cost,
                        actual_cost,
                        quantity,
                        timestamp,
                    ]

                    prescribing_rows.append(row)

        assert seen_practice_with_no_prescribing
        assert seen_practice_with_no_relevant_prescribing
        assert seen_practice_with_no_generic_prescribing
        assert seen_practice_with_no_branded_prescribing

        # In production, normalised_prescribing_standard is actually a view,
        # but for the tests it's much easier to set it up as a normal table.
        table = client.get_or_create_table(
            'normalised_prescribing_standard',
            schemas.PRESCRIBING_SCHEMA
        )

        # Upload prescribing_rows to normalised_prescribing_standard, and
        # create a DataFrame for later verification.
        with tempfile.NamedTemporaryFile() as f:
            writer = csv.writer(f)
            for row in prescribing_rows:
                writer.writerow(row)
            f.seek(0)
            table.insert_rows_from_csv(f.name)

            headers = ['sha', 'regional_team_id', 'stp_id', 'ccg_id',
                       'practice_id', 'bnf_code', 'bnf_name', 'items',
                       'net_cost', 'actual_cost', 'quantity', 'month']
            prescriptions = pd.read_csv(f.name, names=headers)
            prescriptions['month'] = prescriptions['month'].str[:10]

        # Do the work.
        call_command('import_measures', measure='desogestrel')

        # Check calculations by redoing calculations with Pandas, and asserting
        # that results match.
        month = '2018-08-01'
        prescriptions = prescriptions[prescriptions['month'] == month]
        numerators = prescriptions[prescriptions['bnf_code'].str.startswith('0703021Q0B')]
        denominators = prescriptions[prescriptions['bnf_code'].str.startswith('0703021Q0')]
        mg = MeasureGlobal.objects.get(month=month)

        self.assertEqual(MeasureValue.objects.filter(month=month).count(), 780)

        practices = self.calculate_measure(
            numerators,
            denominators,
            'practice',
            Practice.objects.values_list('code', flat=True)
        )
        self.validate_measure_global(mg, practices, 'practice')
        mvs = MeasureValue.objects.filter(
            month=month,
            practice_id__isnull=False,
            pct_id__isnull=False,
            stp_id__isnull=False,
            regional_team_id__isnull=False,
        )
        self.assertEqual(mvs.count(), 625)
        for mv in mvs:
            self.validate_measure_value(mv, practices.loc[mv.practice_id])

        ccgs = self.calculate_measure(
            numerators,
            denominators,
            'ccg',
            PCT.objects.values_list('code', flat=True)
        )
        self.validate_measure_global(mg, ccgs, 'ccg')
        mvs = MeasureValue.objects.filter(
            month=month,
            practice_id__isnull=True,
            pct_id__isnull=False,
            stp_id__isnull=False,
            regional_team_id__isnull=False,
        )
        self.assertEqual(mvs.count(), 125)
        for mv in mvs:
            self.validate_measure_value(mv, ccgs.loc[mv.pct_id])

        stps = self.calculate_measure(
            numerators,
            denominators,
            'stp',
            STP.objects.values_list('ons_code', flat=True)
        )
        self.validate_measure_global(mg, stps, 'stp')
        mvs = MeasureValue.objects.filter(
            month=month,
            practice_id__isnull=True,
            pct_id__isnull=True,
            stp_id__isnull=False,
            regional_team_id__isnull=True,
        )
        self.assertEqual(mvs.count(), 25)
        for mv in mvs:
            self.validate_measure_value(mv, stps.loc[mv.stp_id])

        regtms = self.calculate_measure(
            numerators,
            denominators,
            'regional_team',
            RegionalTeam.objects.values_list('code', flat=True)
        )
        self.validate_measure_global(mg, regtms, 'regional_team')
        mvs = MeasureValue.objects.filter(
            month=month,
            practice_id__isnull=True,
            pct_id__isnull=True,
            stp_id__isnull=True,
            regional_team_id__isnull=False,
        )
        self.assertEqual(mvs.count(), 5)
        for mv in mvs:
            self.validate_measure_value(mv, regtms.loc[mv.regional_team_id])

    def calculate_measure(self, numerators, denominators, org_type, org_codes):
        org_column = org_type + '_id'
        df = pd.DataFrame(index=org_codes)

        df['quantity_total'] = denominators.groupby(org_column)['quantity'].sum()
        df['cost_total'] = denominators.groupby(org_column)['actual_cost'].sum()
        df['quantity_branded'] = numerators.groupby(org_column)['quantity'].sum()
        df['cost_branded'] = numerators.groupby(org_column)['actual_cost'].sum()
        df = df.fillna(0)
        df['quantity_total'] = df['quantity_total'].astype('int')
        df['quantity_branded'] = df['quantity_branded'].astype('int')
        df['quantity_generic'] = df['quantity_total'] - df['quantity_branded']
        df['cost_generic'] = df['cost_total'] - df['cost_branded']
        df['quantity_ratio'] = df['quantity_branded'] / df['quantity_total']
        ranks = df['quantity_ratio'].rank(method='min')
        num_non_nans = df['quantity_ratio'].count()
        df['quantity_ratio_percentile'] = (ranks - 1) / ((num_non_nans - 1) / 100.0)
        global_unit_cost_branded = df['cost_branded'].sum() / df['quantity_branded'].sum()
        global_unit_cost_generic = df['cost_generic'].sum() / df['quantity_generic'].sum()
        df['unit_cost_branded'] = df['cost_branded'] / df['quantity_branded']
        df['unit_cost_generic'] = df['cost_generic'] / df['quantity_generic']
        df['unit_cost_branded'] = df['unit_cost_branded'].fillna(global_unit_cost_branded)
        df['unit_cost_generic'] = df['unit_cost_generic'].fillna(global_unit_cost_generic)
        practice_quantity_ratio_10 = df['quantity_ratio'].quantile(0.1)
        df['quantity_branded_10'] = df['quantity_total'] * practice_quantity_ratio_10
        df['quantity_generic_10'] = df['quantity_total'] - df['quantity_branded_10']
        df['target_cost_10'] = df['unit_cost_branded'] * df['quantity_branded_10'] + df['unit_cost_generic'] * df['quantity_generic_10']
        df['cost_saving_10'] = df['cost_total'] - df['target_cost_10']

        return df

    def validate_measure_global(self, mg, df, org_type):
        self.assertAlmostEqual(
            mg.percentiles[org_type]['10'],
            df['quantity_ratio'].quantile(0.1)
        )
        self.assertAlmostEqual(
            mg.cost_savings[org_type]['10'],
            df[df['cost_saving_10'] > 0]['cost_saving_10'].sum()
        )

    def validate_measure_value(self, mv, series):
        self.assertEqual(mv.numerator, series['quantity_branded'])
        self.assertEqual(mv.denominator, series['quantity_total'])
        if mv.percentile is not None:
            self.assertAlmostEqual(mv.percentile, series['quantity_ratio_percentile'])
            self.assertAlmostEqual(mv.calc_value, series['quantity_ratio'])
        self.assertAlmostEqual(mv.cost_savings['10'], series['cost_saving_10'])
