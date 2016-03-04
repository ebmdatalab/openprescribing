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


class Command(BaseCommand):
    '''
    Just for dosulepin for now.
    Supply either an --end_date argument to load data for
    all months up to that date.
    Or a --month argument to load data for just one month.
    '''
    def add_arguments(self, parser):
        parser.add_argument('--month')
        parser.add_argument('--end_date')

    def handle(self, *args, **options):
        self.IS_VERBOSE = False
        if options['verbosity'] > 1:
            self.IS_VERBOSE = True
        if not options['month'] and not options['end_date']:
            err = 'You must supply either a month, or an end date, '
            err += 'in the format YYYY-MM-DD'
            print err
            sys.exit()

        months = []
        if 'month' in options and options['month']:
            months.append(options['month'])
        else:
            # TODO: Change this back.
            d = datetime(2014, 1, 1)
            end_date = parse(options['end_date'])
            while (d <= end_date):
                months.append(datetime.strftime(d, '%Y-%m-01'))
                d = d + relativedelta(months=1)

        try:
            measure = Measure.objects.get(id='ktt8_dosulepin')
        except ObjectDoesNotExist:
            description = '''
            Number of prescription items for dosulepin as percentage of the
            total number of prescription items for 'selected' antidepressants
            (subset of BNF 4.3)'''
            title = '''
            KTT8 (Dosulepin): First choice antidepressant use in adults with
            depression or anxiety disorder
            '''
            num = 'Number of prescription items for dosulepin (0403010J0)'
            denom = '''
                Number of prescription items for selected
                antidepressants (0403, excluding 0403010B0, 0403010F0,
                0403010N0, 0403010V0, 0403010Y0, 040302, 0403040F0)
            '''
            numerator_short = 'Dosulepin items'
            denominator_short = 'Selected antidepressant items'
            rank = 'mean percentile over the past three months'
            url = 'https://www.nice.org.uk/'
            url += 'advice/ktt8/chapter/evidence-context'
            measure = Measure.objects.create(
                id='ktt8_dosulepin',
                name='KTT8 (Dosulepin)',
                title=title,
                description=description,
                numerator_description=num,
                denominator_description=denom,
                ranking_description=rank,
                numerator_short=numerator_short,
                denominator_short=denominator_short,
                url=url
            )

        if self.IS_VERBOSE:
            print 'creating measure:', measure.title

        # Values by practice by month. Use standard practices only.
        for month in months:
            practices = Practice.objects.filter(setting=4) \
                                        .filter(Q(open_date__isnull=True) |
                                                Q(open_date__lt=month)) \
                                        .filter(Q(close_date__isnull=True) |
                                                Q(close_date__gt=month))
            if self.IS_VERBOSE:
                print month
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
                q = 'SELECT SUM(total_items) as items '
                q += 'FROM frontend_prescription '
                q += "WHERE (presentation_code LIKE '0403010J0%%') "
                q += "AND (practice_id=%s) "
                q += "AND (processing_date=%s)"
                numerator = utils.execute_query(q, [[p.code, month]])
                mv.numerator = numerator[0]['items']

                # Denominator.
                q = 'SELECT SUM(total_items) as items '
                q += 'FROM frontend_prescription '
                q += "WHERE (presentation_code LIKE '0403%%') "
                q += "AND (presentation_code NOT LIKE '0403010B0%%') "
                q += "AND (presentation_code NOT LIKE '0403010F0%%') "
                q += "AND (presentation_code NOT LIKE '0403010N0%%') "
                q += "AND (presentation_code NOT LIKE '0403010V0%%') "
                q += "AND (presentation_code NOT LIKE '0403010Y0%%') "
                q += "AND (presentation_code NOT LIKE '040302%%') "
                q += "AND (presentation_code NOT LIKE '0403040F0%%') "
                q += "AND (practice_id=%s) "
                q += "AND (processing_date=%s)"
                denominator = utils.execute_query(q, [[p.code, month]])
                mv.denominator = denominator[0]['items']

                # Values.
                if mv.denominator:
                    if mv.numerator:
                        mv.calc_value = float(mv.numerator) / \
                            float(mv.denominator)
                    else:
                        mv.calc_value = 0
                else:
                    mv.calc_value = 0

                mv.save()

            records = MeasureValue.objects.filter(month=month)
            records = records.filter(measure=measure).values()
            df = pd.DataFrame.from_records(records)

            if 'calc_value' in df:
                # TODO: Experiment with including and excluding zero values,
                # on real data, and see which produces better results.
                df['rank_val'] = rankdata(df.calc_value.values, method='min')
                df.rank_val = df.rank_val - 1
                df['percentile'] = (df.rank_val / float(len(df)-1)) * 100

                for i, row in df.iterrows():
                    practice = Practice.objects.get(code=row.practice_id)
                    mv = MeasureValue.objects.get(practice=practice,
                                                  month=month)
                    if np.isnan(row.percentile):
                        row.percentile = None
                    mv.percentile = row.percentile
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
                    mg.calc_value = 0
                mg.practice_10th = df.quantile(.1)['calc_value']
                mg.practice_25th = df.quantile(.25)['calc_value']
                mg.practice_50th = df.quantile(.5)['calc_value']
                mg.practice_75th = df.quantile(.75)['calc_value']
                mg.practice_90th = df.quantile(.9)['calc_value']
                mg.save()
