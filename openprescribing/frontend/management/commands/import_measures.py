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
from frontend.models import Measure, MeasureGlobal,  MeasureValue, Practice, PCT
from scipy.stats import rankdata


class Command(BaseCommand):
    '''
    Supply either --end_date to load data for all months
    up to that date, or --month to load data for just one
    month. You can also supply --start_date.
    '''
    def add_arguments(self, parser):
        parser.add_argument('--month')
        parser.add_argument('--start_date')
        parser.add_argument('--end_date')
        parser.add_argument('--measure')
        parser.add_argument('--definitions_only', action='store_true')

    def handle(self, *args, **options):
        options = self.parse_options(options)
        for m in options['measure_ids']:
            measure_config = options['measures'][m]
            measure = self.create_or_update_measure(m, measure_config)
            if options['definitions_only']:
                continue
            for month in options['months']:
                # Create practice values and percentiles. Use these to calculate
                # global values and percentiles. Then calculate cost savings
                # for individual practices, and globally.
                self.create_practice_measurevalues(measure, month, measure_config)
                records = MeasureValue.objects.filter(month=month)\
                            .filter(measure=measure).values()
                df = self.create_dataframe_with_ranks_and_percentiles(records)
                mg = self.create_or_update_measureglobal(df, measure, month, 'practice')
                for i, row in df.iterrows():
                    self.set_percentile_and_savings(row, measure, month, mg, 'practice')
                if measure.is_cost_based:
                    self.set_measureglobal_savings(mg)

                # Now calculate CCG values, percentiles and cost savings.
                self.create_ccg_measurevalues(measure, month)
                ccg_records = MeasureValue.objects.filter(month=month)\
                            .filter(measure=measure, practice=None).values()
                df = self.create_dataframe_with_ranks_and_percentiles(ccg_records)
                mg = self.create_or_update_measureglobal(df, measure, month, 'ccg')
                for i, row in df.iterrows():
                    self.set_percentile_and_savings(row, measure, month, mg, 'ccg')

    def parse_options(self, options):
        self.IS_VERBOSE = False
        if options['verbosity'] > 1:
            self.IS_VERBOSE = True
        fpath = os.path.dirname(__file__)
        files = glob.glob(fpath + "/measure_definitions/*.json")
        options['measures'] = {}
        for fname in files:
            fname = os.path.join(fpath, fname)
            json_data=open(fname).read()
            d = json.loads(json_data)
            for k in d:
                if k in options['measures']:
                    sys.exit()
                    print "duplicate entry found!", k
                else:
                    options['measures'][k] = d[k]
        if 'measure' in options and options['measure']:
            options['measure_ids'] = [options['measure']]
        else:
            options['measure_ids'] = [k for k in measures]

        # Get months to cover from options.
        if not options['month'] and not options['end_date']:
            err = 'You must supply either --month or --end_date '
            err += 'in the format YYYY-MM-DD. You can also '
            err += 'optionally supply a start date.'
            print err
            sys.exit()
        options['months'] = []
        if 'month' in options and options['month']:
            options['months'] = [options['month']]
        else:
            if 'start_date' in options and options['start_date']:
                d = parse(options['start_date'])
            else:
                d = datetime(2014, 1, 1)
            end_date = parse(options['end_date'])
            while (d <= end_date):
                options['months'].append(datetime.strftime(d, '%Y-%m-01'))
                d = d + relativedelta(months=1)
        return options

    def create_or_update_measure(self, m, v):
        if self.IS_VERBOSE:
            print 'Updating measure:', m
        v['description'] = ' '.join(v['description'])
        v['num'] = ' '.join(v['num'])
        v['denom'] = ' '.join(v['denom'])
        v['num_sql'] = ' '.join(v['num_sql'])
        v['denom_sql'] = ' '.join(v['denom_sql'])
        try:
            measure = Measure.objects.get(id=m)
            measure.name = v['name']
            measure.title = v['title']
            measure.description = v['description']
            measure.numerator_description = v['num']
            measure.denominator_description = v['denom']
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
                numerator_short=v['numerator_short'],
                denominator_short=v['denominator_short'],
                url=v['url'],
                is_cost_based=v['is_cost_based'],
                is_percentage=v['is_percentage']
            )
        return measure

    def create_practice_measurevalues(self, measure, month, measure_config):
        if self.IS_VERBOSE:
            print 'updating', measure.title, 'for practices in', month
        # Calculate values only for standard practices that were open
        # in each month, to avoid messing up percentile calculations.
        practices = Practice.objects.filter(setting=4) \
                                    .filter(Q(open_date__isnull=True) |
                                            Q(open_date__lt=month)) \
                                    .filter(Q(close_date__isnull=True) |
                                            Q(close_date__gt=month))
        for practice in practices:
            self.create_measurevalue(measure, practice, month,
                                     measure_config['num_sql'],
                                     measure_config['denom_sql'])

    def create_ccg_measurevalues(self, measure, month):
        if self.IS_VERBOSE:
            print 'updating', measure.title, 'for CCGs in', month
        pcts = PCT.objects.filter(org_type='CCG') \
            .filter(Q(open_date__isnull=True) |
                    Q(open_date__lt=month)) \
            .filter(Q(close_date__isnull=True) |
                    Q(close_date__gt=month))
        for pct in pcts:
            mvs = MeasureValue.objects.filter(
                measure=measure,
                pct=pct,
                practice__isnull=False,
                month=month
            )
            try:
                mv_pct = MeasureValue.objects.get(
                    measure=measure,
                    pct=pct,
                    practice=None,
                    month=month
                )
            except ObjectDoesNotExist:
                mv_pct = MeasureValue.objects.create(
                    measure=measure,
                    pct=pct,
                    practice=None,
                    month=month
                )
            mv_pct.numerator = mvs.aggregate(Sum('numerator')).values()[0]
            mv_pct.denominator = mvs.aggregate(Sum('denominator')).values()[0]
            mv_pct.num_items = mvs.aggregate(Sum('num_items')).values()[0]
            mv_pct.denom_items = mvs.aggregate(Sum('denom_items')).values()[0]
            mv_pct.num_cost = mvs.aggregate(Sum('num_cost')).values()[0]
            mv_pct.denom_cost = mvs.aggregate(Sum('denom_cost')).values()[0]
            mv_pct.num_quantity = mvs.aggregate(Sum('num_quantity')).values()[0]
            mv_pct.denom_quantity = mvs.aggregate(Sum('denom_quantity')).values()[0]
            mv_pct.calc_value = self.get_calc_value(mv_pct.numerator, mv_pct.denominator)
            mv_pct.save()

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
        # CCG calculations match *current* practice membership.
        mv.pct = p.ccg
        numerator = utils.execute_query(num_sql, [[p.code, month]])
        if numerator:
            d = numerator[0]
            if d['numerator']:
                mv.numerator = float(d['numerator'])
            else:
                mv.numerator = 0
            if 'items' in d and d['items']:
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
            if 'items' in d and d['items']:
                mv.denom_items = float(d['items'])
            if 'cost' in d and d['cost']:
                mv.denom_cost = float(d['cost'])
            if 'quantity' in d and d['quantity']:
                mv.denom_quantity = float(d['quantity'])
        else:
            mv.denominator = None
        mv.calc_value = self.get_calc_value(mv.numerator, mv.denominator)
        mv.save()

    def set_percentile_and_savings(self, row, measure, month, mg, org_type):
        '''
        NB: This assumes that we always use quantity to calculate savings,
        not items. This means our numerator and denominator need to be
        directly comparable in quantity terms.
        '''
        if org_type == 'practice':
            practice = Practice.objects.get(code=row.practice_id)
            mv = MeasureValue.objects.get(practice=practice,
                                          month=month,
                                          measure=measure)
        else:
            pct = PCT.objects.get(code=row.pct_id)
            mv = MeasureValue.objects.get(practice=None, pct=pct,
                                          month=month,
                                          measure=measure)
        if (row.percentile is None) or np.isnan(row.percentile):
            row.percentile = None
        mv.percentile = row.percentile
        if measure.is_cost_based:
            row_quantity = row.denom_quantity
            row_cost = row.denom_cost
            centiles = [10, 25, 50, 75, 90]
            for c in centiles:
                ratio = getattr(mg, '%s_%sth' % (org_type, c))
                num_quant = row_quantity * ratio
                non_num_quant = row_quantity - num_quant
                cost_of_new_quant = (num_quant * mg.cost_per_num_quant) + \
                    (non_num_quant * mg.cost_per_non_num_quant)
                saving = row_cost - cost_of_new_quant
                setattr(mv, 'cost_saving_%sth' % c, saving)
        mv.save()

    def create_dataframe_with_ranks_and_percentiles(self, records):
        '''
        Use scipy's rankdata to rank by calc_value - we use rankdata rather than
        pandas qcut because pandas qcut does not cope well with repeated values
        (e.g. repeated values of zero). Returns dataframe with percentile column.
        '''
        if self.IS_VERBOSE:
            print 'processing dataframe of length', len(records)
        df = pd.DataFrame.from_records(records)
        # Skip empty dataframes.
        if 'calc_value' in df:
            # Rank by calc_value, skipping nulls.
            df.loc[df['calc_value'].notnull(), 'rank_val'] = \
                rankdata(df[df.calc_value.notnull()].calc_value.values,
                         method='min') - 1
            df1 = df[df['rank_val'].notnull()]
            # Add percentiles to each row, and normalise to 0-100 to make
            # comparisons easier later.
            df.loc[df['rank_val'].notnull(), 'percentile'] = \
                (df1.rank_val / float(len(df1)-1)) * 100
            # TODO: Still needed?
            cols = ['num_items', 'num_cost', 'num_quantity',
                    'denom_items', 'denom_cost', 'denom_quantity']
            df[cols] = df[cols].fillna(0)
            return df
        else:
            return None

    def create_or_update_measureglobal(self, df, measure, month, org_type):
        '''
        Given the ranked dataframe of all practices, create or
        update the MeasureGlobal percentiles for that month.
        We don't strictly need to use pandas methods for
        the numerator/denominator sums, but do so for ease.
        '''
        mg, created = MeasureGlobal.objects.get_or_create(
            measure=measure,
            month=month
        )
        if org_type == 'practice':
            mg.numerator = df['numerator'].sum()
            if np.isnan(mg.numerator):
                mg.numerator = None
            mg.denominator = df['denominator'].sum()
            if np.isnan(mg.denominator):
                mg.denominator = None
            mg.calc_value = self.get_calc_value(mg.numerator, mg.denominator)
            mg.practice_10th = df.quantile(.1)['calc_value']
            mg.practice_25th = df.quantile(.25)['calc_value']
            mg.practice_50th = df.quantile(.5)['calc_value']
            mg.practice_75th = df.quantile(.75)['calc_value']
            mg.practice_90th = df.quantile(.9)['calc_value']
            # Create global summed items, quantity etc. TODO: Still needed?
            aggregates = ['num_items', 'denom_items', 'num_cost',
                'denom_cost', 'num_quantity', 'denom_quantity']
            for a in aggregates:
                if a in df.columns:
                    setattr(mg, a, df[a].sum())
        else:
            mg.ccg_10th = df.quantile(.1)['calc_value']
            mg.ccg_25th = df.quantile(.25)['calc_value']
            mg.ccg_50th = df.quantile(.5)['calc_value']
            mg.ccg_75th = df.quantile(.75)['calc_value']
            mg.ccg_90th = df.quantile(.9)['calc_value']
        mg.save()
        # Temporary attributes, not saved in the database.
        if measure.is_cost_based:
            mg.cost_per_num_quant = mg.num_cost / mg.num_quantity
            mg.cost_per_non_num_quant = (mg.denom_cost - mg.num_cost) / \
                (mg.denom_quantity - mg.num_quantity)
        return mg

    def get_calc_value(self, numerator, denominator):
        calc_value = None
        if denominator:
            if numerator:
                calc_value = float(numerator) / \
                    float(denominator)
            else:
                calc_value = numerator
        return calc_value

    def set_measureglobal_savings(self, mg):
        mvs = MeasureValue.objects.filter(measure=mg.measure, month=mg.month)
        mg.cost_saving_10th = mvs.filter(cost_saving_10th__gt=0).aggregate(Sum('cost_saving_10th')).values()[0]
        mg.cost_saving_25th = mvs.filter(cost_saving_25th__gt=0).aggregate(Sum('cost_saving_25th')).values()[0]
        mg.cost_saving_50th = mvs.filter(cost_saving_50th__gt=0).aggregate(Sum('cost_saving_50th')).values()[0]
        mg.cost_saving_75th = mvs.filter(cost_saving_75th__gt=0).aggregate(Sum('cost_saving_75th')).values()[0]
        mg.cost_saving_90th = mvs.filter(cost_saving_90th__gt=0).aggregate(Sum('cost_saving_90th')).values()[0]
        mg.save()
