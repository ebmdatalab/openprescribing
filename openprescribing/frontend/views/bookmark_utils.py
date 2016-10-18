import numpy as np

from dateutil.relativedelta import relativedelta
from frontend.models import ImportLog
from frontend.models import Measure
from frontend.models import MeasureValue


def remove_jagged(measurevalues):
    """Remove records that are outside the standard error of the mean or
    where they hit 0% or 100% more than once.

    Bit of a guess as to if this'll work or not. Pending review by
    real statistician.

    """
    values = [x.percentile for x in measurevalues]
    sem = (np.std(values) /
           np.sqrt(len(values)))
    keep = []
    extremes = 0
    for x in measurevalues:
        if x.measure.is_percentage:
            if x.calc_value == 1.0:
                extremes += 1
        if x.calc_value == 0.0:
            extremes += 1
        if x.numerator and x.numerator < 15:
            extremes += 1
        if extremes > 1 or x.percentile < sem or x.percentile > (100 - sem):
            next
        else:
            keep.append(x)
    return keep


def remove_jagged_logit(measurevalues):
    """Remove records that are outside the standard error of the mean.

    Bit of a guess as to if this'll work or not. Pending review by
    real statistivcian.

    """
    values = []
    for m in measurevalues:
        val = m.percentile / 100.0
        if val > 0 and val < 1:
            values.append(np.log(val/(100-val)))
        else:
            values.append(
                np.log(
                    (val + 0.5/len(measurevalues))/
                    (1 - val + (0.5/len(measurevalues)))
                )
            )
    sem = (np.std(values) /
           np.sqrt(len(values)))
    keep = []
    for m in measurevalues:
        if m.percentile < sem or m.percentile > (100 - sem):
            next
        else:
            keep.append(m)
    return keep


class InterestingMeasureFinder(object):
    def __init__(self, practice=None, pct=None,
                 interesting_saving=1000,
                 interesting_percentile_change=10):
        assert practice or pct
        self.practice = practice
        self.pct = pct
        self.interesting_percentile_change = interesting_percentile_change
        self.interesting_saving = interesting_saving

    def months_ago(self, period):
        now = ImportLog.objects.latest_in_category('prescribing').current_at
        return now + relativedelta(months=-(period-1))

    def _best_or_worst_performing_in_period(self, period, best_or_worst=None):
        assert best_or_worst in ['best', 'worst']
        worst = []
        for measure in Measure.objects.all():
            measure_filter = {
                'measure': measure, 'month__gte': self.months_ago(period)}
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
            is_worst = remove_jagged(
                MeasureValue.objects.filter(**measure_filter))
            if len(is_worst) == period:
                worst.append(measure.id)
        return worst

    def worst_performing_in_period(self, period):
        """Return every measure where the organisation specified in the given
        bookmark is in the worst decile for each month in the
        specified time range

        """
        return self._best_or_worst_performing_in_period(period, 'worst')

    def best_performing_in_period(self, period):
        """Return every measure where organisations specified in the given
        bookmark is in the best decile for each month in the specified
        time range

        """
        return self._best_or_worst_performing_in_period(period, 'best')

    def most_change_in_period(self, period):
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
                'month__gte': self.months_ago(period),
                'percentile__isnull': False
            }
            if self.practice:
                measure_filter['practice'] = self.practice
            else:
                measure_filter['pct'] = self.pct
                measure_filter['practice'] = None
            percentiles = [x.percentile for x in
                           remove_jagged(
                               MeasureValue.objects.filter(**measure_filter)
                               .order_by('month'))]
            if len(percentiles) == period:
                x = np.arange(period)
                y = np.array(percentiles)
                p, res, _, _, _ = np.polyfit(x, y, 1, full=True)
                m, b = p
                slope_of_interest = (
                    self.interesting_percentile_change /
                    float(period - 1)
                )
                if res < 1200:
                    if m > 0 and m >= slope_of_interest \
                       or m < 0 and m <= -slope_of_interest:
                        lines_of_best_fit.append(
                            (m, b, m * (period - 1) + b,
                             measure.id, res[0]))
        lines_of_best_fit = sorted(lines_of_best_fit, key=lambda x: x[0])
        return [(line[3], line[1], line[2], line[4])
                for line in lines_of_best_fit]

    def most_change_in_period_2(self, period):
        most_changing = []
        for measure in Measure.objects.all():
            measure_filter = {
                'measure': measure,
                'month__gte': self.months_ago(period),
                'percentile__isnull': False
            }
            if self.practice:
                measure_filter['practice'] = self.practice
            else:
                measure_filter['pct'] = self.pct
                measure_filter['practice'] = None
            percentiles = [x.percentile for x in
                           remove_jagged(
                               MeasureValue.objects.filter(**measure_filter)
                               .order_by('month'))]
            if len(percentiles) == period:
                split = period / 2
                d1 = np.array(percentiles[:split])
                d2 = np.array(percentiles[split:])
                d1_mean = np.mean(d1)
                d2_mean = np.mean(d2)
                percentile_change = d1_mean - d2_mean
                if percentile_change >= self.interesting_percentile_change or \
                   percentile_change <= (
                       0 - self.interesting_percentile_change):
                    most_changing.append(
                        (percentile_change, measure.id, d1_mean, d2_mean)
                    )

        most_changing = sorted(most_changing, key=lambda x: x[0])
        return [(line[1], line[2], line[3])
                for line in most_changing]

    def top_and_total_savings_in_period(self, period):
        """Sum total possible savings over time, and find measures where
        possible or achieved savings are greater than self.interesting_saving.

        Returns a dictionary where the keys are
        `possible_top_savings_total`, `possible_savings` and
        `achieved_savings`; and the values are an integer, sorted
        `(measure, saving)` tuples, and sorted `(measure, saving)`
        tuples respectively.

        """
        possible_savings = []
        achieved_savings = []
        total_savings = 0
        for measure in Measure.objects.all():
            if measure.is_cost_based:
                # XXX factor out this conditional filtering
                measure_filter = {
                    'measure': measure, 'month__gte': self.months_ago(period)}
                if self.practice:
                    measure_filter['practice'] = self.practice
                else:
                    measure_filter['pct'] = self.pct
                    measure_filter['practice'] = None
                values = list(
                    MeasureValue.objects.filter(**measure_filter))
                if len(values) != period:
                    continue
                savings_at_50th = [
                    x.cost_savings['50'] for x in
                    values]
                possible_savings_for_measure = sum(
                    [x for x in savings_at_50th if x > 0])
                savings_or_loss_for_measure = sum(savings_at_50th)
                if possible_savings_for_measure >= self.interesting_saving:
                    possible_savings.append(
                        (measure.id, possible_savings_for_measure)
                    )
                if savings_or_loss_for_measure <= -self.interesting_saving:
                    achieved_savings.append(
                        (measure.id, -1 * savings_or_loss_for_measure))
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
            'worst': self.worst_performing_in_period(3),
            'best': self.best_performing_in_period(3),
            'most_changing': self.most_change_in_period(9),
            'top_savings': self.top_and_total_savings_in_period(6)}


def test_debug():
    from frontend.models import PCT
    from frontend.models import Practice
    import json
    print "Data for 100 CCGs:"
    with open("/tmp/ccgs.json", "w") as f:
        for ccg in PCT.objects.all()[:100]:
            finder = InterestingMeasureFinder(
                pct=ccg)
            result = {}
            result['url'] = "https://openprescribing.net/ccg/" + ccg.code
            result['data'] = finder.context_for_org_email()
            f.write(json.dumps(result) + "\n")
    print "Data for 10 Practices:"
    with open("/tmp/practices.json", "w") as f:
        for practice in Practice.objects.all()[:1000]:
            finder = InterestingMeasureFinder(
                practice=practice)
            result = {}
            result['url'] = "https://openprescribing.net/practice/" + practice.code
            result['data'] = finder.context_for_org_email()
            f.write(json.dumps(result) + "\n")

def test_debug2():
    from frontend.models import PCT
    from frontend.models import Practice
    import json
    f = open("/tmp/data-6-month-method-1.json", "w")
    for ccg in PCT.objects.all():
        finder = InterestingMeasureFinder(
            pct=ccg, interesting_percentile_change=20)
        result = {}
        result['data'] = finder.most_change_in_period(6)
        result['url'] = "https://openprescribing.net/ccg/" + ccg.code
        f.write(json.dumps(result) + "\n")
    f.close()
    f = open("/tmp/data-6-month-method-2.json", "w")
    for ccg in PCT.objects.all():
        finder = InterestingMeasureFinder(
            pct=ccg, interesting_percentile_change=20)
        result = {}
        result['data'] = finder.most_change_in_period_2(6)
        result['url'] = "https://openprescribing.net/ccg/" + ccg.code
        f.write(json.dumps(result) + "\n")
    f.close()
    f = open("/tmp/data-12-month-method-1.json", "w")
    for ccg in PCT.objects.all():
        finder = InterestingMeasureFinder(
            pct=ccg, interesting_percentile_change=20)
        result = {}
        result['data'] = finder.most_change_in_period(12)
        result['url'] = "https://openprescribing.net/ccg/" + ccg.code
        f.write(json.dumps(result) + "\n")
    f.close()
    f = open("/tmp/data-12-month-method-2.json", "w")
    for ccg in PCT.objects.all():
        finder = InterestingMeasureFinder(
            pct=ccg, interesting_percentile_change=20)
        result = {}
        result['data'] = finder.most_change_in_period_2(12)
        result['url'] = "https://openprescribing.net/ccg/" + ccg.code
        f.write(json.dumps(result) + "\n")
    f.close()
