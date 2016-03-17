from django.core.management.base import BaseCommand, CommandError
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q
from frontend.models import Measure, MeasureGlobal,  MeasureValue, Practice
import api.view_utils as utils
from datetime import datetime
from dateutil.parser import *
from dateutil.relativedelta import *
import numpy as np
import pandas as pd
from scipy.stats import rankdata
import sys


measures = {
    'rosuvastatin': {
        'name': 'Rosuvastatin vs. Atorvastatin',
        'title': 'Rosuvastatin vs. Atorvastatin',
        'description': (
            "Statins are the most commonly prescribed class of drug in the UK. "
            "Atorvastatin and Rosuvastatin are members of this class, and are "
            "both high-potency statins. There will always be reasons why "
            "occasional patients do better with a particular drug, but "
            "overall there is no good evidence that Rosuvastatin is "
            "better than atorvastatin. It is, however, vastly more expensive. "
            "When atorvastatin came off patent, and became cheap, practices "
            "tended to switch people away from expensive Rosuvastatin. "
        ),
        'num': 'Number of prescription items for Rosuvastatin (0212000AA)',
        'denom': (
            "Number of prescription items for Atorvastatin (Atorvastatin)"
        ),
        'numerator_short': 'Rosuvastatin items',
        'denominator_short': 'Atorvastatin items',
        'rank': 'mean percentile over the past three months',
        'url': None,
        'num_sql': (
            "SELECT SUM(total_items) as items, "
            "SUM(actual_cost) as cost "
            "FROM frontend_prescription "
            "WHERE (presentation_code LIKE '0212000AA%%') "
            "AND (practice_id=%s) "
            "AND (processing_date=%s) "
            ),
        'denom_sql': (
            "SELECT SUM(total_items) as items, "
            "SUM(actual_cost) as cost "
            "FROM frontend_prescription "
            "WHERE (presentation_code LIKE '0212000B0%%') "
            "AND (practice_id=%s) "
            "AND (processing_date=%s) "
        ),
        'is_cost_based': True
    },
    'ktt8_dosulepin': {
        'name': 'KTT8 (Dosulepin)',
        'description': (
            "Number of prescription items for dosulepin as percentage of the "
            "total number of prescription items for 'selected' antidepressants "
            "(subset of BNF 4.3)"
        ),
        'title': (
            "KTT8 (Dosulepin): First choice antidepressant use in adults with "
            "depression or anxiety disorder"
        ),
        'num': 'Number of prescription items for dosulepin (0403010J0)',
        'denom': (
            "Number of prescription items for selected "
            "antidepressants (0403, excluding 0403010B0, 0403010F0, "
            "0403010N0, 0403010V0, 0403010Y0, 040302, 0403040F0)"
        ),
        'numerator_short': 'Dosulepin items',
        'denominator_short': 'Selected antidepressant items',
        'rank': 'mean percentile over the past three months',
        'url': 'https://www.nice.org.uk/advice/ktt8/chapter/evidence-context',
        'num_sql': (
            "SELECT SUM(total_items) as items "
            "FROM frontend_prescription "
            "WHERE (presentation_code LIKE '0403010J0%%') "
            "AND (practice_id=%s) "
            "AND (processing_date=%s)"
        ),
        'denom_sql': (
            "SELECT SUM(total_items) as items "
            "FROM frontend_prescription "
            "WHERE (presentation_code LIKE '0403%%') "
            "AND (presentation_code NOT LIKE '0403010B0%%') "
            "AND (presentation_code NOT LIKE '0403010F0%%') "
            "AND (presentation_code NOT LIKE '0403010N0%%') "
            "AND (presentation_code NOT LIKE '0403010V0%%') "
            "AND (presentation_code NOT LIKE '0403010Y0%%') "
            "AND (presentation_code NOT LIKE '040302%%') "
            "AND (presentation_code NOT LIKE '0403040F0%%') "
            "AND (practice_id=%s) "
            "AND (processing_date=%s)"
        ),
        'is_cost_based': False
    }
}


class Command(BaseCommand):
    '''
    Supply either an --end_date argument to load data for
    all months up to that date.
    Or a --month argument to load data for just one month.
    '''
    def add_arguments(self, parser):
        parser.add_argument('--month')
        parser.add_argument('--end_date')
        parser.add_argument('--measure')

    def handle(self, *args, **options):
        self.IS_VERBOSE = False
        if options['verbosity'] > 1:
            self.IS_VERBOSE = True
        if 'measure' in options and options['measure']:
            measure_ids = [options['measure']]
        else:
            measure_ids = [k for k in measures]
        if not options['month'] and not options['end_date']:
            err = 'You must supply either --month or --end_date '
            err += 'in the format YYYY-MM-DD'
            print err
            sys.exit()
        months = []
        if 'month' in options and options['month']:
            months.append(options['month'])
        else:
            d = datetime(2014, 1, 1)
            end_date = parse(options['end_date'])
            while (d <= end_date):
                months.append(datetime.strftime(d, '%Y-%m-01'))
                d = d + relativedelta(months=1)

        for m in measure_ids:
            # Get or create measure.
            v = measures[m]
            try:
                measure = Measure.objects.get(id=m)
            except ObjectDoesNotExist:
                measure = Measure.objects.create(
                    id=m,
                    name=v['name'],
                    title=v['title'],
                    description=v['description'],
                    numerator_description=v['num'],
                    denominator_description=v['denom'],
                    ranking_description=v['rank'],
                    numerator_short=v['numerator_short'],
                    denominator_short=v['denominator_short'],
                    url=v['url'],
                    is_cost_based=v['is_cost_based']
                )

            # Values by practice by month. Use standard practices only.
            for month in months:
                practices = Practice.objects.filter(setting=4) \
                                            .filter(Q(open_date__isnull=True) |
                                                    Q(open_date__lt=month)) \
                                            .filter(Q(close_date__isnull=True) |
                                                    Q(close_date__gt=month))
                if self.IS_VERBOSE:
                    print 'updating', measure.title, 'for', month
                for p in practices:
                    try:
                        mv = MeasureValue.objects.get(
                            measure=measure,
                            practice=p,
                            month=month
                        )
                    except ObjectDoesNotExist:
                        mv = MeasureValue.objects.create(
                            measure=measure,
                            practice=p,
                            month=month
                        )

                    # Update foreign key values to match current
                    # organisational links.
                    mv.pct = p.ccg

                    # Numerator.
                    numerator = utils.execute_query(v['num_sql'], [[p.code, month]])
                    mv.numerator = numerator[0]['items']

                    # Denominator.
                    denominator = utils.execute_query(v['denom_sql'], [[p.code, month]])
                    mv.denominator = denominator[0]['items']

                    # Values.
                    if mv.denominator:
                        if mv.numerator:
                            mv.calc_value = float(mv.numerator) / \
                                float(mv.denominator)
                        else:
                            mv.calc_value = 0
                    else:
                        mv.calc_value = None

                    mv.save()

                records = MeasureValue.objects.filter(month=month)
                records = records.filter(measure=measure).values()
                if self.IS_VERBOSE:
                    print len(records), 'values created'

                df = pd.DataFrame.from_records(records)

                if 'calc_value' in df:
                    df.loc[df['calc_value'].notnull(), 'rank_val'] = \
                        rankdata(df[df.calc_value.notnull()].calc_value.values,
                                 method='min') - 1
                    df1 = df[df['rank_val'].notnull()]
                    df.loc[df['rank_val'].notnull(), 'percentile'] = \
                        (df1.rank_val / float(len(df1)-1)) * 100

                    for i, row in df.iterrows():
                        practice = Practice.objects.get(code=row.practice_id)
                        # print practice, month
                        mv = MeasureValue.objects.get(practice=practice,
                                                      month=month,
                                                      measure=measure)
                        if (row.percentile is None) or np.isnan(row.percentile):
                            row.percentile = None
                        mv.percentile = row.percentile

                        if measure.is_cost_based:
                            mv.cost_saving = 0
                        mv.save()

                    # Finally, global practice percentiles.
                    mg, created = MeasureGlobal.objects.get_or_create(
                        measure=measure,
                        month=month
                    )
                    mg.numerator = df['numerator'].sum()
                    if np.isnan(mg.numerator):
                        mg.numerator = None
                    mg.denominator = df['denominator'].sum()
                    if np.isnan(mg.denominator):
                        mg.denominator = None
                    if mg.denominator:
                        if mg.numerator:
                            mg.calc_value = float(mg.numerator) / \
                                float(mg.denominator)
                        else:
                            mg.calc_value = mg.numerator
                    else:
                        mg.calc_value = None
                    mg.practice_10th = df.quantile(.1)['calc_value']
                    mg.practice_25th = df.quantile(.25)['calc_value']
                    mg.practice_50th = df.quantile(.5)['calc_value']
                    mg.practice_75th = df.quantile(.75)['calc_value']
                    mg.practice_90th = df.quantile(.9)['calc_value']
                    mg.save()
