import datetime
import numpy as np

from dateutil.relativedelta import relativedelta
from frontend.models import ImportLog
from frontend.models import Measure
from frontend.models import MeasureGlobal
from frontend.models import MeasureValue


class InterestingMeasureFinder(object):
    def __init__(self, org_bookmark, since_months):
        self.org_bookmark = org_bookmark
        self.since_months = since_months
        now = ImportLog.objects.latest_in_category('prescribing').current_at
        self.months_ago = now + relativedelta(months=-self.since_months)

    def _best_or_worst_performing_over_time(self, best_or_worst=None):
        assert best_or_worst in ['best', 'worst']
        # Where they're in the worst decile over the past six months,
        # ordered by badness
        worst = []
        for measure in Measure.objects.all():
            percentiles = MeasureGlobal.objects.filter(
                measure=measure, month__gte=self.months_ago
            ).only('month', 'percentiles')
            if len(percentiles) < self.since_months:
                percentiles = []
            for p in percentiles:
                measure_filter = {
                    'measure': measure,
                    'month': p.month
                }
                if self.org_bookmark.practice:
                    measure_filter['practice'] = self.org_bookmark.practice
                    entity_type = 'practice'
                else:
                    measure_filter['pct'] = self.org_bookmark.pct
                    measure_filter['practice'] = None
                    entity_type = 'ccg'
                if measure.low_is_good:
                    if best_or_worst == 'worst':
                        measure_filter['percentile__gte'] = \
                          p.percentiles[entity_type]['90'] * 100
                    else:
                        measure_filter['percentile__lte'] = \
                          p.percentiles[entity_type]['10'] * 100
                else:
                    if best_or_worst == 'worst':
                        measure_filter['percentile__lte'] = \
                          p.percentiles[entity_type]['10'] * 100
                    else:
                        measure_filter['percentile__gte'] = \
                          p.percentiles[entity_type]['90'] * 100
                is_worst = MeasureValue.objects.filter(**measure_filter)
                if is_worst.count() == 0:
                    worst = []
                    break
                else:
                    worst.append(measure)
        return worst

    def worst_performing_over_time(self):
        """Return every measure where the organisation specified in the given
        bookmark is in the worst decile for each month in the
        specified time range

        """
        return self._best_or_worst_performing_over_time('worst')

    def best_performing_over_time(self):
        """Return every measure where organisations specified in the given
        bookmark is in the best decile for each month in the specified
        time range

        """
        return self._best_or_worst_performing_over_time('best')

    def most_change_over_time(self):
        """Every measure where the specified organisation has changed by more
        than 10 centiles in the specified time period, ordered by rate
        of change.

        The rate of change is worked out using a line of best fit.

        Returns a list of triples of (measure, change_from, change_to)

        """
        lines_of_best_fit = []
        for measure in Measure.objects.all():
            measure_filter = {'measure': measure, 'month__gte': self.months_ago}
            if self.org_bookmark.practice:
                measure_filter['practice'] = self.org_bookmark.practice
            else:
                measure_filter['pct'] = self.org_bookmark.pct
                measure_filter['practice'] = None
            percentiles = [x.percentile for x in
                           MeasureValue.objects.filter(**measure_filter)
                           .order_by('month')]
            if len(percentiles) == self.since_months:
                x = np.arange(self.since_months)
                y = np.array(percentiles)
                m, b = np.polyfit(x, y, 1)
                slope_of_interest = 10.0 / self.since_months
                if m > 0 and m >= slope_of_interest \
                   or m < 0 and m <= -slope_of_interest:
                    lines_of_best_fit.append((m, b, measure))
        lines_of_best_fit = sorted(lines_of_best_fit, key=lambda x: x[0])
        # XXX probably should be a dictionary with two sets of
        # triples, like the next function
        return [(line[2], b, m * (self.since_months - 1) + b)
                for line in lines_of_best_fit]

    def top_and_total_savings_over_time(self):
        """Sum total possible savings over time, and find measures where
        possible or achieved savings are greater than 1000.

        Returns a dictionary where the keys are
        `possible_top_savings_total`, `possible_savings` and
        `achieved_savings`; and the values are an integer, sorted
        `(measure, saving)` tuples, and sorted `(measure, saving)`
        tuples respectively.

        """
        # Top savings for CCG, where savings are greater than GBP1000 .
        possible_savings = []
        achieved_savings = []
        total_savings = 0
        for measure in Measure.objects.all():
            if measure.is_cost_based:
                # XXX factor out this conditional filtering
                measure_filter = {
                    'measure': measure, 'month__gte': self.months_ago}
                if self.org_bookmark.practice:
                    measure_filter['practice'] = self.org_bookmark.practice
                else:
                    measure_filter['pct'] = self.org_bookmark.pct
                    measure_filter['practice'] = None
                values = list(MeasureValue.objects.filter(**measure_filter))
                if len(values) < self.since_months:
                    continue
                savings_at_50th = [
                    x.cost_savings['50'] for x in
                    values]
                possible_savings_for_measure = sum(
                    [x for x in savings_at_50th if x > 0])
                savings_or_loss_for_measure = sum(savings_at_50th)
                if possible_savings_for_measure >= 1000:
                    possible_savings.append(
                        (measure, possible_savings_for_measure)
                    )
                if savings_or_loss_for_measure <= -1000:
                    achieved_savings.append(
                        (measure, -1 * savings_or_loss_for_measure))
                if measure.low_is_good:
                    savings_at_10th = sum([
                        max(0, x.cost_savings['10']) for x in
                        values])
                else:
                    savings_at_10th = sum([
                        max(0, x.cost_savings['90']) for x in
                        values])

            total_savings += savings_at_10th
        return {
            'possible_savings': sorted(
                possible_savings, key=lambda x: -x[1]),
            'achieved_savings': sorted(
                achieved_savings, key=lambda x: x[1]),
            'possible_top_savings_total': total_savings
        }

    def context_for_org_email(self):
        return {
            'worst': self.worst_performing_over_time(),
            'best': self.best_performing_over_time(),
            'fastest_worsening': self.fastest_worsening_over_time(),
            'top_savings': self.top_savings_over_time(),
            'total_possible_savings': self.total_possible_savings_over_time()}
