from django.core.management.base import BaseCommand, CommandError
from django.core.exceptions import ObjectDoesNotExist
from frontend.models import Measure, MeasureGlobal,  MeasureValue, Practice
import api.view_utils as utils
import numpy as np
import pandas as pd


class Command(BaseCommand):
    '''
    Just for dosulepin for now.
    '''

    def add_arguments(self, parser):
        parser.add_argument('--month')

    def handle(self, *args, **options):
        self.IS_VERBOSE = False
        if options['verbosity'] > 1:
            self.IS_VERBOSE = True

        # TODO: Figure out how to handle months better.
        if 'month' in options:
            months = [options['month']]
        else:
            for y in range(2010, 2016):
                for m in range(1, 13):
                    if (y == 2010) and m < 8:
                        continue
                    if (y == 2015) and m > 10:
                        continue
                    month = '%s-%s-01' % (y, ('0%s' % (m)) if m < 10 else m)
                    months.append(month)

        try:
            measure = Measure.objects.get(id='ktt8_dosulepin')
        except ObjectDoesNotExist:
            description = '''
            "Number of prescription items for dosulepin as percentage of the
            total number of prescription items for 'selected' antidepressants
            (subset of BNF 4.3)",
            '''
            title = '''
            KTT8: First choice antidepressant use in adults with depression
            or anxiety disorder
            '''
            measure = Measure.objects.create(
                id='ktt8_dosulepin',
                name='KTT8: Dosulepin: % items',
                title=title,
                description=description
            )

        # Values by practice by month. Use standard practices only.
        practices = Practice.objects.filter(setting=4)
        for month in months:
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
                        mv.calc_value = mv.numerator
                else:
                    mv.calc_value = None
                mv.save()

        # Now calculate percentiles per practice.
        for month in months:
            records = MeasureValue.objects.filter(month=month)
            records = records.filter(measure=measure).values()
            df = pd.DataFrame.from_records(records)

            if 'calc_value' in df:
                df['percentile'] = pd.qcut(df.calc_value, 100, labels=False)
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
                mg.practice_10th = df.quantile(.1)['calc_value']
                mg.practice_25th = df.quantile(.25)['calc_value']
                mg.practice_50th = df.quantile(.5)['calc_value']
                mg.practice_75th = df.quantile(.75)['calc_value']
                mg.practice_90th = df.quantile(.9)['calc_value']
                mg.save()
