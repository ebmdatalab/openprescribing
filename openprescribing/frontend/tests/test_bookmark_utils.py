import datetime
from dateutil.relativedelta import relativedelta

from django.test import TransactionTestCase

from frontend.models import ImportLog
from frontend.models import Measure
from frontend.models import MeasureGlobal
from frontend.models import MeasureValue
from frontend.models import OrgBookmark
from frontend.models import PCT
from frontend.models import Practice
from frontend.models import User
from frontend.views import bookmark_utils


class TestBookmarkUtilsPerforming(TransactionTestCase):
    fixtures = ['bookmark_alerts', 'measures']

    def setUp(self):
        self.measure = Measure.objects.get(pk='cerazette')
        self.measure.low_is_good = True
        self.measure.save()
        pct = PCT.objects.get(pk='03V')
        practice_with_high_percentiles = Practice.objects.get(pk='P87629')
        practice_with_low_percentiles = Practice.objects.get(pk='P87630')
        ImportLog.objects.create(
            category='prescribing',
            current_at=datetime.datetime.today())
        for i in range(3):
            month = datetime.datetime.today() + relativedelta(months=i)
            MeasureValue.objects.create(
                measure=self.measure,
                practice=None,
                pct=pct,
                percentile=95,
                month=month
            )
            MeasureValue.objects.create(
                measure=self.measure,
                practice=practice_with_high_percentiles,
                pct=pct,
                percentile=95,
                month=month
            )
            MeasureValue.objects.create(
                measure=self.measure,
                practice=practice_with_low_percentiles,
                pct=pct,
                percentile=5,
                month=month
            )
        self.pct = pct
        self.high_percentile_practice = practice_with_high_percentiles
        self.low_percentile_practice = practice_with_low_percentiles

    ## Worst performing
    # CCG bookmarks
    def test_hit_where_ccg_worst_in_specified_number_of_months(self):
        finder = bookmark_utils.InterestingMeasureFinder(
            pct=self.pct, month_window=3)
        worst_measures = finder.worst_performing_over_time()
        self.assertIn(self.measure, worst_measures)

    def test_miss_where_not_better_in_specified_number_of_months(self):
        self.measure.low_is_good = False
        self.measure.save()
        finder = bookmark_utils.InterestingMeasureFinder(
            pct=self.pct, month_window=3)
        worst_measures = finder.worst_performing_over_time()
        self.assertFalse(worst_measures)

    def test_miss_where_not_enough_global_data(self):
        finder = bookmark_utils.InterestingMeasureFinder(
            pct=self.pct, month_window=6)
        worst_measures = finder.worst_performing_over_time()
        self.assertFalse(worst_measures)

    def test_miss_where_not_worst_in_specified_number_of_months(self):
        MeasureValue.objects.all().delete()
        finder = bookmark_utils.InterestingMeasureFinder(
            pct=self.pct, month_window=3)
        worst_measures = finder.worst_performing_over_time()
        self.assertFalse(worst_measures)

    # Practice bookmarks
    def test_hit_where_practice_worst_in_specified_number_of_months(self):
        finder = bookmark_utils.InterestingMeasureFinder(
            practice=self.high_percentile_practice, month_window=3)
        worst_measures = finder.worst_performing_over_time()
        self.assertIn(self.measure, worst_measures)

    ## Best performing
    def test_hit_where_practice_best_in_specified_number_of_months(self):
        finder = bookmark_utils.InterestingMeasureFinder(
            practice=self.low_percentile_practice,
            month_window=3)
        best_measures = finder.best_performing_over_time()
        self.assertIn(self.measure, best_measures)


class TestBookmarkUtilsChanging(TransactionTestCase):
    fixtures = ['bookmark_alerts', 'measures']

    def setUp(self):
        self.measure = Measure.objects.get(pk='cerazette')
        ImportLog.objects.create(
            category='prescribing',
            current_at=datetime.datetime.today())
        practice_with_high_change = Practice.objects.get(pk='P87629')
        practice_with_high_neg_change = Practice.objects.get(pk='P87631')
        practice_with_low_change = Practice.objects.get(pk='P87630')
        for i in range(3):
            month = datetime.datetime.today() + relativedelta(months=i)
            MeasureValue.objects.create(
                measure=self.measure,
                practice=practice_with_high_change,
                percentile=i * 10,
                month=month
            )
            MeasureValue.objects.create(
                measure=self.measure,
                practice=practice_with_high_neg_change,
                percentile=i * -10,
                month=month
            )
            MeasureValue.objects.create(
                measure=self.measure,
                practice=practice_with_low_change,
                percentile=i,
                month=month
            )
        self.practice_with_low_change = practice_with_low_change
        self.practice_with_high_change = practice_with_high_change
        self.practice_with_high_neg_change = practice_with_high_neg_change

    def test_low_change_not_returned(self):
        finder = bookmark_utils.InterestingMeasureFinder(
            practice=self.practice_with_low_change,
            month_window=3)
        self.assertEqual(finder.most_change_over_time(), [])

    def test_high_change_returned(self):
        finder = bookmark_utils.InterestingMeasureFinder(
            practice=self.practice_with_high_change,
            month_window=3)
        sorted_measure = finder.most_change_over_time()[0]
        self.assertEqual(sorted_measure[0], self.measure)
        self.assertAlmostEqual(sorted_measure[1], 0)
        self.assertAlmostEqual(sorted_measure[2], 20)

    def test_high_negative_change_returned(self):
        finder = bookmark_utils.InterestingMeasureFinder(
            practice=self.practice_with_high_neg_change,
            month_window=3)
        sorted_measure = finder.most_change_over_time()[0]
        self.assertEqual(sorted_measure[0], self.measure)
        self.assertAlmostEqual(sorted_measure[1], 0)
        self.assertAlmostEqual(sorted_measure[2], -20)


def _makeCostSavingMeasureValues(measure, practice, savings):
    """Create measurevalues for the given practice and measure with
    savings at the 50th centile taken from the specified `savings`
    array.  Savings at the 90th centile are set as 100 times those at
    the 50th, and at the 10th as 0.1 times.

    """
    for i in range(len(savings)):
        month = datetime.datetime.today() + relativedelta(months=i)
        MeasureValue.objects.create(
            measure=measure,
            practice=practice,
            cost_savings={
                '10': savings[i] * 0.1,
                '50': savings[i],
                '90': savings[i] * 100, },
            month=month
        )


class TestBookmarkUtilsSavingsPossible(TransactionTestCase):
    fixtures = ['bookmark_alerts', 'measures']

    def setUp(self):
        self.measure = Measure.objects.get(pk='cerazette')
        ImportLog.objects.create(
            category='prescribing',
            current_at=datetime.datetime.today())
        self.practice = Practice.objects.get(pk='P87629')
        _makeCostSavingMeasureValues(
            self.measure, self.practice, [0, 1500, 2000])

    def test_possible_savings(self):
        finder = bookmark_utils.InterestingMeasureFinder(
            practice=self.practice,
            month_window=3)
        savings = finder.top_and_total_savings_over_time()
        self.assertEqual(savings['possible_savings'], [(self.measure, 3500)])
        self.assertEqual(savings['achieved_savings'], [])
        self.assertEqual(savings['possible_top_savings_total'], 350000)

    def test_possible_savings_low_is_good(self):
        self.measure.low_is_good = True
        self.measure.save()
        finder = bookmark_utils.InterestingMeasureFinder(
            practice=self.practice,
            month_window=3)
        savings = finder.top_and_total_savings_over_time()
        self.assertEqual(savings['possible_savings'], [(self.measure, 3500)])
        self.assertEqual(savings['achieved_savings'], [])
        self.assertEqual(savings['possible_top_savings_total'], 350.0)


class TestBookmarkUtilsSavingsAchieved(TransactionTestCase):
    fixtures = ['bookmark_alerts', 'measures']

    def setUp(self):
        self.measure = Measure.objects.get(pk='cerazette')
        ImportLog.objects.create(
            category='prescribing',
            current_at=datetime.datetime.today())
        self.practice = Practice.objects.get(pk='P87629')
        _makeCostSavingMeasureValues(
            self.measure, self.practice, [-1000, -500, 100])

    def test_achieved_savings(self):
        finder = bookmark_utils.InterestingMeasureFinder(
            practice=self.practice,
            month_window=3)
        savings = finder.top_and_total_savings_over_time()
        self.assertEqual(savings['possible_savings'], [])
        self.assertEqual(savings['achieved_savings'], [(self.measure, 1400)])
        self.assertEqual(savings['possible_top_savings_total'], 10000)
