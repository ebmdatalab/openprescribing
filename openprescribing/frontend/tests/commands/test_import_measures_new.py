from __future__ import print_function

import csv
import tempfile
from random import randint

import numpy as np
import pandas as pd

from django.core.management import call_command
from django.test import TestCase

from frontend import bq_schemas as schemas
from frontend.models import (
    ImportLog,
    Measure,
    MeasureGlobal,
    MeasureValue,
    Practice,
    PCT,
    STP,
    RegionalTeam,
)
from gcutils.bigquery import Client


# These tests test import_measures by repeating the measure calculations with
# Pandas, and asserting that the values stored on MeasureValue and
# MeasureGlobal objects match those calculated with Pandas.  See
# notebooks/measure-calculations.ipynb for an explanation of these
# calculations.

class ImportMeasuresTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        create_organisations()
        set_up_bq()
        cls.prescriptions = upload_prescribing()
        cls.practice_statistics = upload_practice_statistics()

        # import_measures uses this ImportLog to work out which months it
        # should import data.
        ImportLog.objects.create(category='prescribing', current_at='2018-08-01')

    def test_cost_based_percentage_measure(self):
        # This test verifies the behaviour of import_measures for a cost-based
        # measure that calculates the ratio between:
        #  * quantity prescribed of a branded presentation (numerator)
        #  * total quantity prescribed of the branded presentation and its
        #      generic equivalent (denominator)

        # Do the work.
        call_command('import_measures', measure='desogestrel')

        # Check that numerator_bnf_codes has been set
        m = Measure.objects.get(id='desogestrel')
        self.assertEqual(m.numerator_bnf_codes, ['0703021Q0BBAAAA'])

        # Check calculations by redoing calculations with Pandas, and asserting
        # that results match.
        month = '2018-08-01'
        prescriptions = self.prescriptions[self.prescriptions['month'] == month]
        numerators = prescriptions[
            prescriptions['bnf_code'].str.startswith('0703021Q0B')
        ]
        denominators = prescriptions[
            prescriptions['bnf_code'].str.startswith('0703021Q0')
        ]
        self.validate_calculations(
            self.calculate_cost_based_percentage_measure,
            numerators,
            denominators,
            month
        )

    def test_practice_statistics_measure(self):
        # This test verifies the behaviour of import_measures for a measure
        # that calculates the ratio between:
        #  * items prescribed of a particular presentation (numerator)
        #  * patients / 1000 (denominator)
        #
        # Of interest is the case where the number of patients may be null for
        # a given practice in a given month.  See #1520.

        # Do the work.
        call_command('import_measures', measure='coproxamol')

        # Check calculations by redoing calculations with Pandas, and asserting
        # that results match.
        month = '2018-08-01'
        prescriptions = self.prescriptions[self.prescriptions['month'] == month]
        numerators = prescriptions[prescriptions['bnf_code'] == '0407010Q0AAAAAA']
        denominators = self.practice_statistics[self.practice_statistics['month'] == month]
        self.validate_calculations(
            self.calculate_practice_statistics_measure,
            numerators,
            denominators,
            month
        )

    def test_cost_based_practice_statistics_measure(self):
        # This test verifies the behaviour of import_measures for a cost-based
        # measure that calculates the ratio between:
        #  * cost of prescribing of a particular presentation (numerator)
        #  * patients / 1000 (denominator)

        # Do the work.
        call_command('import_measures', measure='glutenfree')

        # Check calculations by redoing calculations with Pandas, and asserting
        # that results match.
        month = '2018-08-01'
        prescriptions = self.prescriptions[self.prescriptions['month'] == month]
        numerators = prescriptions[prescriptions['bnf_code'] == '0904010AUBBAAAA']
        denominators = self.practice_statistics[self.practice_statistics['month'] == month]
        self.validate_calculations(
            self.calculate_cost_based_practice_statistics_measure,
            numerators,
            denominators,
            month
        )

    def calculate_cost_based_percentage_measure(
        self, numerators, denominators, org_type, org_codes
    ):
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
        global_unit_cost_branded = (
            df['cost_branded'].sum() / df['quantity_branded'].sum()
        )
        global_unit_cost_generic = (
            df['cost_generic'].sum() / df['quantity_generic'].sum()
        )
        df['unit_cost_branded'] = df['cost_branded'] / df['quantity_branded']
        df['unit_cost_generic'] = df['cost_generic'] / df['quantity_generic']
        df['unit_cost_branded'] = df['unit_cost_branded'].fillna(
            global_unit_cost_branded
        )
        df['unit_cost_generic'] = df['unit_cost_generic'].fillna(
            global_unit_cost_generic
        )
        quantity_ratio_10 = df['quantity_ratio'].quantile(0.1)
        df['quantity_branded_10'] = df['quantity_total'] * quantity_ratio_10
        df['quantity_generic_10'] = df['quantity_total'] - df['quantity_branded_10']
        df['target_cost_10'] = (
            df['unit_cost_branded'] * df['quantity_branded_10']
            + df['unit_cost_generic'] * df['quantity_generic_10']
        )
        df['cost_saving_10'] = df['cost_total'] - df['target_cost_10']

        return pd.DataFrame.from_dict({
            'numerator' : df['quantity_branded'],
            'denominator': df['quantity_total'],
            'ratio': df['quantity_ratio'],
            'ratio_percentile': df['quantity_ratio_percentile'],
            'cost_saving_10': df['cost_saving_10'],
        })

    def calculate_practice_statistics_measure(
        self, numerators, denominators, org_type, org_codes
    ):
        org_column = org_type + '_id'
        df = pd.DataFrame(index=org_codes)

        df['items'] = numerators.groupby(org_column)['items'].sum()
        df['thousand_patients'] = (
            denominators.groupby(org_column)['total_list_size'].sum() / 1000
        )
        df['ratio'] = df['items'] / df['thousand_patients']
        df['items'] = df['items'].fillna(0)
        df['thousand_patients'] = df['thousand_patients'].fillna(0)
        ranks = df['ratio'].rank(method='min')
        num_non_nans = df['ratio'].count()
        df['ratio_percentile'] = (ranks - 1) / ((num_non_nans - 1) / 100.0)

        return pd.DataFrame.from_dict({
            'numerator' : df['items'],
            'denominator': df['thousand_patients'],
            'ratio': df['ratio'],
            'ratio_percentile': df['ratio_percentile'],
        })

    def calculate_cost_based_practice_statistics_measure(
        self, numerators, denominators, org_type, org_codes
    ):
        org_column = org_type + '_id'
        df = pd.DataFrame(index=org_codes)

        df['cost'] = numerators.groupby(org_column)['actual_cost'].sum()
        df['thousand_patients'] = (
            denominators.groupby(org_column)['total_list_size'].sum() / 1000
        )
        df['ratio'] = df['cost'] / df['thousand_patients']
        df['cost'] = df['cost'].fillna(0)
        df['thousand_patients'] = df['thousand_patients'].fillna(0)
        ranks = df['ratio'].rank(method='min')
        num_non_nans = df['ratio'].count()
        df['ratio_percentile'] = (ranks - 1) / ((num_non_nans - 1) / 100.0)
        ratio_10 = df['ratio'].quantile(0.1)
        df['target_cost_10'] = ratio_10 * df['thousand_patients']
        df['cost_saving_10'] = df['cost'] - df['target_cost_10']

        return pd.DataFrame.from_dict({
            'numerator' : df['cost'],
            'denominator': df['thousand_patients'],
            'ratio': df['ratio'],
            'ratio_percentile': df['ratio_percentile'],
            'cost_saving_10': df['cost_saving_10'],
        })

    def validate_calculations(self, calculator, numerators, denominators, month):
        '''Validate measure calculations by redoing calculations with Pandas.'''

        mg = MeasureGlobal.objects.get(month=month)

        practices = calculator(
            numerators,
            denominators,
            'practice',
            Practice.objects.values_list('code', flat=True),
        )
        self.validate_measure_global(mg, practices, 'practice')
        mvs = MeasureValue.objects.filter(
            month=month,
            practice_id__isnull=False,
            pct_id__isnull=False,
            stp_id__isnull=False,
            regional_team_id__isnull=False,
        )
        self.assertEqual(mvs.count(), Practice.objects.count())
        for mv in mvs:
            self.validate_measure_value(mv, practices.loc[mv.practice_id])

        ccgs = calculator(
            numerators, denominators, 'ccg', PCT.objects.values_list('code', flat=True)
        )
        self.validate_measure_global(mg, ccgs, 'ccg')
        mvs = MeasureValue.objects.filter(
            month=month,
            practice_id__isnull=True,
            pct_id__isnull=False,
            stp_id__isnull=False,
            regional_team_id__isnull=False,
        )
        self.assertEqual(mvs.count(), PCT.objects.count())
        for mv in mvs:
            self.validate_measure_value(mv, ccgs.loc[mv.pct_id])

        stps = calculator(
            numerators,
            denominators,
            'stp',
            STP.objects.values_list('ons_code', flat=True),
        )
        self.validate_measure_global(mg, stps, 'stp')
        mvs = MeasureValue.objects.filter(
            month=month,
            practice_id__isnull=True,
            pct_id__isnull=True,
            stp_id__isnull=False,
            regional_team_id__isnull=True,
        )
        self.assertEqual(mvs.count(), STP.objects.count())
        for mv in mvs:
            self.validate_measure_value(mv, stps.loc[mv.stp_id])

        regtms = calculator(
            numerators,
            denominators,
            'regional_team',
            RegionalTeam.objects.values_list('code', flat=True),
        )
        self.validate_measure_global(mg, regtms, 'regional_team')
        mvs = MeasureValue.objects.filter(
            month=month,
            practice_id__isnull=True,
            pct_id__isnull=True,
            stp_id__isnull=True,
            regional_team_id__isnull=False,
        )
        self.assertEqual(mvs.count(), RegionalTeam.objects.count())
        for mv in mvs:
            self.validate_measure_value(mv, regtms.loc[mv.regional_team_id])

    def validate_measure_global(self, mg, df, org_type):
        self.assertAlmostEqual(
            mg.percentiles[org_type]['10'], df['ratio'].quantile(0.1)
        )
        if mg.measure.is_cost_based:
            self.assertAlmostEqual(
                mg.cost_savings[org_type]['10'],
                df[df['cost_saving_10'] > 0]['cost_saving_10'].sum(),
            )

    def validate_measure_value(self, mv, series):
        self.assertAlmostEqual(mv.numerator, series['numerator'])
        self.assertAlmostEqual(mv.denominator, series['denominator'])
        if mv.percentile is None:
            self.assertTrue(np.isnan(series['ratio']))
            self.assertTrue(np.isnan(series['ratio_percentile']))
        else:
            self.assertAlmostEqual(mv.calc_value, series['ratio'])
            self.assertAlmostEqual(mv.percentile, series['ratio_percentile'])

        if mv.measure.is_cost_based:
            self.assertAlmostEqual(mv.cost_savings['10'], series['cost_saving_10'])


def create_organisations():
    '''Create RegionalTeams, STPs, CCGs, Practices'''

    for regtm_ix in range(5):
        regtm = RegionalTeam.objects.create(
            code='Y0{}'.format(regtm_ix), name='Region {}'.format(regtm_ix)
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
                    code='{}{}{}'.format(regtm_ix, stp_ix, ccg_ix).replace(
                        '0', 'A'
                    ),
                    name='CCG {}/{}/{}'.format(regtm_ix, stp_ix, ccg_ix),
                    org_type='CCG',
                )

                for prac_ix in range(5):
                    Practice.objects.create(
                        ccg=ccg,
                        code='P0{}{}{}{}'.format(regtm_ix, stp_ix, ccg_ix, prac_ix),
                        name='Practice {}/{}/{}/{}'.format(
                            regtm_ix, stp_ix, ccg_ix, prac_ix
                        ),
                        setting=4,
                    )


def set_up_bq():
    '''Set up BQ, and upload CCGs and practices.'''

    Client('measures').create_dataset()
    client = Client('hscic')
    table = client.get_or_create_table('ccgs', schemas.CCG_SCHEMA)
    columns = [field.name for field in schemas.CCG_SCHEMA]
    table.insert_rows_from_pg(PCT, columns, schemas.ccgs_transform)
    table = client.get_or_create_table('practices', schemas.PRACTICE_SCHEMA)
    columns = [field.name for field in schemas.PRACTICE_SCHEMA]
    table.insert_rows_from_pg(Practice, columns)


def upload_prescribing():
    '''Generate prescribing data, and upload to BQ.'''

    prescribing_rows = []

    # These are for the desogestrel measure
    presentations = [
        ('0703021Q0AAAAAA', 'Desogestrel_Tab 75mcg'),  # generic
        ('0703021Q0BBAAAA', 'Cerazette_Tab 75mcg'),  # branded
        ('076543210AAAAAA', 'Etynodiol Diacet_Tab 500mcg'),  # irrelevant
    ]

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
                actual_cost = (1 + ix) * randint(100, 200) * quantity * 0.01

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

    # These are for the coproxamol and glutenfree measures
    presentations = [
        ('0407010Q0AAAAAA', 'Co-Proxamol_Tab 32.5mg/325mg'),
        ('0904010AUBBAAAA', "Mrs Crimble's_G/F W/F Cheese Bites Orig"),
    ]

    for practice in Practice.objects.all():
        for month in [7, 8]:
            timestamp = '2018-0{}-01 00:00:00 UTC'.format(month)

            for bnf_code, bnf_name in presentations:
                items = randint(0, 100)
                quantity = randint(6, 28) * items

                actual_cost = randint(100, 200) * quantity * 0.01

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

    # In production, normalised_prescribing_standard is actually a view,
    # but for the tests it's much easier to set it up as a normal table.
    table = Client('hscic').get_or_create_table(
        'normalised_prescribing_standard', schemas.PRESCRIBING_SCHEMA
    )

    with tempfile.NamedTemporaryFile() as f:
        writer = csv.writer(f)
        for row in prescribing_rows:
            writer.writerow(row)
        f.seek(0)
        table.insert_rows_from_csv(f.name)

        headers = [
            'sha',
            'regional_team_id',
            'stp_id',
            'ccg_id',
            'practice_id',
            'bnf_code',
            'bnf_name',
            'items',
            'net_cost',
            'actual_cost',
            'quantity',
            'month',
        ]
        prescriptions = pd.read_csv(f.name, names=headers)
        prescriptions['month'] = prescriptions['month'].str[:10]

    return prescriptions


def upload_practice_statistics():
    '''Generate practice statistics data, and upload to BQ.'''

    practice_statistics_rows = []
    seen_practice_with_no_statistics = False
    columns = [
        'month',
        'regional_team_id',
        'stp_id',
        'ccg_id',
        'practice_id',
        'total_list_size',
    ]
    practice_statistics = pd.DataFrame(columns=columns)

    for practice in Practice.objects.all():
        for month in [7, 8]:
            timestamp = '2018-0{}-01 00:00:00 UTC'.format(month)

            if month == 8 and practice.code == 'P00000':
                seen_practice_with_no_statistics = True
                continue

            total_list_size = randint(100, 200)

            row = [
                timestamp,  #  month
                0,  #  male_0_4
                0,  #  female_0_4
                0,  #  male_5_14
                0,  #  male_15_24
                0,  #  male_25_34
                0,  #  male_35_44
                0,  #  male_45_54
                0,  #  male_55_64
                0,  #  male_65_74
                0,  #  male_75_plus
                0,  #  female_5_14
                0,  #  female_15_24
                0,  #  female_25_34
                0,  #  female_35_44
                0,  #  female_45_54
                0,  #  female_55_64
                0,  #  female_65_74
                0,  #  female_75_plus
                total_list_size,  #  total_list_size
                0,  #  astro_pu_cost
                0,  #  astro_pu_items
                '{}',  #  star_pu
                practice.ccg_id,  #  pct_id
                practice.code,  #  practice
            ]

            practice_statistics_rows.append(row)
            practice_statistics = practice_statistics.append(
                {
                    'month': timestamp[:10],
                    'practice_id': practice.code,
                    'ccg_id': practice.ccg_id,
                    'stp_id': practice.ccg.stp_id,
                    'regional_team_id': practice.ccg.regional_team_id,
                    'total_list_size': total_list_size,
                },
                ignore_index=True,
            )

    assert seen_practice_with_no_statistics

    # Upload practice_statistics_rows to BigQuery.
    table = Client('hscic').get_or_create_table(
        'practice_statistics', schemas.PRACTICE_STATISTICS_SCHEMA
    )

    with tempfile.NamedTemporaryFile() as f:
        writer = csv.writer(f)
        for row in practice_statistics_rows:
            writer.writerow(row)
        f.seek(0)
        table.insert_rows_from_csv(f.name)

    return practice_statistics
