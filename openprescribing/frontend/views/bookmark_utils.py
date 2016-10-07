import numpy as np

from dateutil.relativedelta import relativedelta
from frontend.models import ImportLog
from frontend.models import Measure
from frontend.models import MeasureValue


class InterestingMeasureFinder(object):
    def __init__(self, practice=None, pct=None,
                 month_window=6,
                 interesting_saving=1000,
                 interesting_percentile_change=10):
        assert practice or pct
        self.practice = practice
        self.pct = pct
        self.month_window = month_window
        self.interesting_percentile_change = interesting_percentile_change
        self.interesting_saving = interesting_saving
        now = ImportLog.objects.latest_in_category('prescribing').current_at
        self.months_ago = now + relativedelta(months=-(self.month_window-1))

    def _best_or_worst_performing_over_time(self, best_or_worst=None):
        assert best_or_worst in ['best', 'worst']
        worst = []
        for measure in Measure.objects.all():
            measure_filter = {
                'measure': measure, 'month__gte': self.months_ago}
            if self.practice:
                measure_filter['practice'] = self.practice
            else:
                measure_filter['pct'] = self.pct
                measure_filter['practice'] = None
            if measure.low_is_good:
                if best_or_worst == 'worst':
                    measure_filter['percentile__gte'] = 90
                else:
                    measure_filter['percentile__lte'] = 10
            else:
                if best_or_worst == 'worst':
                    measure_filter['percentile__lte'] = 10
                else:
                    measure_filter['percentile__gte'] = 90
            is_worst = MeasureValue.objects.filter(**measure_filter)
            if is_worst.count() == self.month_window:
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
            measure_filter = {
                'measure': measure,
                'month__gte': self.months_ago,
                'percentile__isnull': False
            }
            if self.practice:
                measure_filter['practice'] = self.practice
            else:
                measure_filter['pct'] = self.pct
                measure_filter['practice'] = None
            percentiles = [x.percentile for x in
                           MeasureValue.objects.filter(**measure_filter)
                           .order_by('month')]
            if len(percentiles) == self.month_window:
                x = np.arange(self.month_window)
                y = np.array(percentiles)
                m, b = np.polyfit(x, y, 1)
                slope_of_interest = (
                    self.interesting_percentile_change /
                    float(self.month_window)
                )
                if m > 0 and m >= slope_of_interest \
                   or m < 0 and m <= -slope_of_interest:
                    lines_of_best_fit.append(
                        (m, b, m * (self.month_window - 1) + b, measure))
        lines_of_best_fit = sorted(lines_of_best_fit, key=lambda x: x[0])
        # XXX probably should be a dictionary with two sets of
        # triples, like the next function
        return [(line[3], line[1], line[2])
                for line in lines_of_best_fit]

    def top_and_total_savings_over_time(self):
        """Sum total possible savings over time, and find measures where
        possible or achieved savings are greater than self.interesting_saving.

        Returns a dictionary where the keys are
        `possible_top_savings_total`, `possible_savings` and
        `achieved_savings`; and the values are an integer, sorted
        `(measure, saving)` tuples, and sorted `(measure, saving)`
        tuples respectively.

        """
        # Top savings for CCG, where savings are greater than GBPself.interesting_saving .
        possible_savings = []
        achieved_savings = []
        total_savings = 0
        for measure in Measure.objects.all():
            if measure.is_cost_based:
                # XXX factor out this conditional filtering
                measure_filter = {
                    'measure': measure, 'month__gte': self.months_ago}
                if self.practice:
                    measure_filter['practice'] = self.practice
                else:
                    measure_filter['pct'] = self.pct
                    measure_filter['practice'] = None
                values = list(MeasureValue.objects.filter(**measure_filter))
                if len(values) != self.month_window:
                    continue
                savings_at_50th = [
                    x.cost_savings['50'] for x in
                    values]
                possible_savings_for_measure = sum(
                    [x for x in savings_at_50th if x > 0])
                savings_or_loss_for_measure = sum(savings_at_50th)
                if possible_savings_for_measure >= self.interesting_saving:
                    possible_savings.append(
                        (measure, possible_savings_for_measure)
                    )
                if savings_or_loss_for_measure <= -self.interesting_saving:
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
            'most_changing': self.most_change_over_time(),
            'top_savings': self.top_and_total_savings_over_time()}

def test_debug():
    from frontend.models import PCT
    from frontend.models import Practice
    print "Data for 10 CCGs:"
    for ccg in PCT.objects.all()[:50]:
        finder = InterestingMeasureFinder(
            pct=ccg, month_window=6)
        print ccg, "https://openprescribing.net/ccg/" + ccg.code
        print finder.context_for_org_email()
    print "Data for 10 Practices:"
    for practice in Practice.objects.all()[:50]:
        finder = InterestingMeasureFinder(
            practice=practice, month_window=6)
        print practice, "https://openprescribing.net/practice/" + practice.code
        print finder.context_for_org_email()
