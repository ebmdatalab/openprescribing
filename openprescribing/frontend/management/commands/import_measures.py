import json
import glob
import numpy as np
import os
import pandas as pd
import sys
import api.view_utils as utils
from datetime import datetime
from dateutil.parser import *
from dateutil.relativedelta import *
from django.core.management.base import BaseCommand, CommandError
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Sum, Q
from frontend.models import Measure, MeasureGlobal,  MeasureValue, Practice
from scipy.stats import rankdata



class Command(BaseCommand):
    '''
    Supply either an --end_date argument to load data for
    all months up to that date.
    Or a --month argument to load data for just one month.
    '''
    def add_arguments(self, parser):
        parser.add_argument('--month')
        parser.add_argument('--start_date')
        parser.add_argument('--end_date')
        parser.add_argument('--measure')
        parser.add_argument('--definitions_only', action='store_true')

    def handle(self, *args, **options):
        self.IS_VERBOSE = False
        if options['verbosity'] > 1:
            self.IS_VERBOSE = True

        # Get measure definitions to use - either an individual
        # measure supplied in an option, or all measures in
        # the JSON files.
        fpath = os.path.dirname(__file__)
        files = glob.glob(fpath + "/measure_definitions/*.json")
        measures = {}
        for fname in files:
            fname = os.path.join(fpath, fname)
            json_data=open(fname).read()
            d = json.loads(json_data)
            for k in d:
                if k in measures:
                    sys.exit()
                    print "duplicate entry found!", k
                else:
                    measures[k] = d[k]
        if 'measure' in options and options['measure']:
            measure_ids = [options['measure']]
        else:
            measure_ids = [k for k in measures]

        # Get months to cover from options.
        if not options['month'] and not options['end_date']:
            err = 'You must supply either --month or --end_date '
            err += 'in the format YYYY-MM-DD. You can also '
            err += 'optionally supply a start date.'
            print err
            sys.exit()
        months = []
        if 'month' in options and options['month']:
            months.append(options['month'])
        else:
            if 'start_date' in options and options['start_date']:
                d = parse(options['start_date'])
            else:
                d = datetime(2014, 1, 1)
            end_date = parse(options['end_date'])
            while (d <= end_date):
                months.append(datetime.strftime(d, '%Y-%m-01'))
                d = d + relativedelta(months=1)

        # Now, for every measure that we care about...
        for m in measure_ids:
            if self.IS_VERBOSE:
                print 'Updating measure:', m

            v = measures[m]
            v['description'] = ' '.join(v['description'])
            v['num'] = ' '.join(v['num'])
            v['denom'] = ' '.join(v['denom'])
            v['num_sql'] = ' '.join(v['num_sql'])
            v['denom_sql'] = ' '.join(v['denom_sql'])

            # Create or update the measure.
            try:
                measure = Measure.objects.get(id=m)
                measure.name = v['name']
                measure.title = v['title']
                measure.description = v['description']
                measure.numerator_description = v['num']
                measure.numerator_description = v['denom']
                measure.numerator_short = v['numerator_short']
                measure.denominator_short = v['denominator_short']
                measure.url = v['url']
                measure.is_cost_based = v['is_cost_based']
                measure.is_percentage = v['is_percentage']
                measure.save()
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
                    is_cost_based=v['is_cost_based'],
                    is_percentage=v['is_percentage']
                )

            if 'definitions_only' in options and options['definitions_only']:
                continue

            # For all months, set the measurevalue for all practices.
            for month in months:
                # We're interested in all standard practices that were
                # operating that month.
                practices = Practice.objects.filter(setting=4) \
                                            .filter(Q(open_date__isnull=True) |
                                                    Q(open_date__lt=month)) \
                                            .filter(Q(close_date__isnull=True) |
                                                    Q(close_date__gt=month))
                if self.IS_VERBOSE:
                    print 'updating', measure.title, 'for', month

                for p in practices:
                    # print p.code
                    # Set the raw values of the measure.
                    self.create_measurevalue(measure, p, month,
                                             v['num_sql'],
                                             v['denom_sql'])

            # once we've done the raw calculations, calculate individual
            # practice percentiles, global percentiles, cost savings
            # for each practice, then global cost savings.
            # the percentile for each practice, the global percentiles,
            # the cost savings for each practice based on the global
            # percentiles, and then the
            for month in months:
                records = MeasureValue.objects.filter(month=month)\
                            .filter(measure=measure).values()
                df = self.rank_and_set_percentiles(records)
                mg = self.create_measureglobal(df, measure, month)
                if measure.is_cost_based:
                    mg.cost_per_num_quant = mg.num_cost / mg.num_quantity
                    mg.cost_per_non_num_quant = (mg.denom_cost - mg.num_cost) / \
                        (mg.denom_quantity - mg.num_quantity)
                for i, row in df.iterrows():
                    self.set_practice_percentile_and_savings(row, measure,
                                                                month, mg)
                self.set_global_cost_savings(mg)

    def create_measurevalue(self, measure, p, month, num_sql, denom_sql):
        '''
        Given a practice and the definition of a measure, calculate
        the measure's values for a particular month.
        '''
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
        # Values should match *current* organisational hierarchy.
        mv.pct = p.ccg
        numerator = utils.execute_query(num_sql, [[p.code, month]])
        if numerator:
            d = numerator[0]
            if d['numerator']:
                mv.numerator = float(d['numerator'])
            else:
                mv.numerator = 0
            if d['items'] and d['items']:
                mv.num_items = float(d['items'])
            if 'cost' in d and d['cost']:
                mv.num_cost = float(d['cost'])
            if 'quantity' in d and d['quantity']:
                mv.num_quantity = float(d['quantity'])
        else:
            mv.numerator = None
        denominator = utils.execute_query(denom_sql, [[p.code, month]])
        if denominator:
            d = denominator[0]
            if d['denominator']:
                mv.denominator = float(d['denominator'])
            else:
                mv.denominator = 0
            if d['items'] and d['items']:
                mv.denom_items = float(d['items'])
            if 'cost' in d and d['cost']:
                mv.denom_cost = float(d['cost'])
            if 'quantity' in d and d['quantity']:
                mv.denom_quantity = float(d['quantity'])
        else:
            mv.denominator = None
        if mv.denominator:
            if mv.numerator:
                mv.calc_value = mv.numerator / mv.denominator
            else:
                mv.calc_value = 0
        else:
            if mv.numerator:
                mv.calc_value = float('inf') # near infinity... hack
            else:
                mv.calc_value = None
        mv.save()

    def set_practice_percentile_and_savings(self, row, measure, month, mg):
        practice = Practice.objects.get(code=row.practice_id)
        mv = MeasureValue.objects.get(practice=practice,
                                      month=month,
                                      measure=measure)
        if (row.percentile is None) or np.isnan(row.percentile):
            row.percentile = None
        mv.percentile = row.percentile
        if measure.is_cost_based:
            total_quantity = row.denom_quantity
            total_cost = row.denom_cost
            mv.cost_saving_10th = self._get_savings_at_ratio(mg.practice_10th,
                total_quantity, total_cost, mg)
            mv.cost_saving_25th = self._get_savings_at_ratio(mg.practice_25th,
                total_quantity, total_cost, mg)
            mv.cost_saving_50th = self._get_savings_at_ratio(mg.practice_50th,
                total_quantity, total_cost, mg)
            mv.cost_saving_75th = self._get_savings_at_ratio(mg.practice_75th,
                total_quantity, total_cost, mg)
            mv.cost_saving_90th = self._get_savings_at_ratio(mg.practice_90th,
                total_quantity, total_cost, mg)
        mv.save()

    def _get_savings_at_ratio(self, ratio, total_quantity, total_cost, mg):
        '''
        NB: This assumes that we always use quantity to calculate savings,
        not items. This means our numerator and denominator need to be
        comparable in quantity terms.
        '''
        num_quant = total_quantity * ratio
        non_num_quant = total_quantity - num_quant
        cost_of_new_quant = (num_quant * mg.cost_per_num_quant) + \
            (non_num_quant * mg.cost_per_non_num_quant)
        return total_cost - cost_of_new_quant

    def rank_and_set_percentiles(self, records):
        '''
        Use scipy's rankdata to rank by calc_value - we use rankdata rather than
        pandas qcut because pandas qcut does not cope well with repeated values
        (e.g. repeated values of zero, which we will have a lot of).
        Lastly, we normalise percentiles between 0 and 100 to make comparisons
        easier later.
        '''
        if self.IS_VERBOSE:
            print 'processing dataframe of length', len(records)
        df = pd.DataFrame.from_records(records)
        if 'calc_value' in df:
            df.loc[df['calc_value'].notnull(), 'rank_val'] = \
                rankdata(df[df.calc_value.notnull()].calc_value.values,
                         method='min') - 1
            df1 = df[df['rank_val'].notnull()]
            df.loc[df['rank_val'].notnull(), 'percentile'] = \
                (df1.rank_val / float(len(df1)-1)) * 100
            # Replace NaNs with 0s in numeric columns.
            cols = ['num_items', 'num_cost', 'num_quantity',
                    'denom_items', 'denom_cost', 'denom_quantity']
            df[cols] = df[cols].fillna(0)
            return df
        else:
            return None

    def create_measureglobal(self, df, measure, month):
        '''
        Given the ranked dataframe of all practices, create or
        update the MeasureGlobal percentiles for that month.
        '''
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
        aggregates = ['num_items', 'denom_items', 'num_cost',
            'denom_cost', 'num_quantity', 'denom_quantity']
        for a in aggregates:
            if a in df.columns:
                setattr(mg, a, df[a].sum())
        mg.save()
        return mg

    def set_global_cost_savings(self, mg):
        mvs = MeasureValue.objects.filter(measure=mg.measure, month=mg.month)
        mg.cost_saving_10th = mvs.filter(cost_saving_10th__gt=0).aggregate(Sum('cost_saving_10th')).values()[0]
        mg.cost_saving_25th = mvs.filter(cost_saving_25th__gt=0).aggregate(Sum('cost_saving_25th')).values()[0]
        mg.cost_saving_50th = mvs.filter(cost_saving_50th__gt=0).aggregate(Sum('cost_saving_50th')).values()[0]
        mg.cost_saving_75th = mvs.filter(cost_saving_75th__gt=0).aggregate(Sum('cost_saving_75th')).values()[0]
        mg.cost_saving_90th = mvs.filter(cost_saving_90th__gt=0).aggregate(Sum('cost_saving_90th')).values()[0]
        mg.save()
