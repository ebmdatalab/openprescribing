import datetime

from django.test import TestCase

from frontend.models import MeasureValue, MeasureGlobal


class MeasureValueManagerTests(TestCase):
    fixtures = ['one_month_of_measures']

    def test_by_regional_team_with_no_org(self):
        mvs = MeasureValue.objects.by_regional_team([])
        self.assertEqual(len(mvs), 2)

    def test_by_regional_team_with_org(self):
        mvs = MeasureValue.objects.by_regional_team(['Y01'])
        self.assertEqual(len(mvs), 1)

    def test_by_regional_team_with_orgs(self):
        mvs = MeasureValue.objects.by_regional_team(['Y01', 'Y02'])
        self.assertEqual(len(mvs), 2)

    def test_by_regional_team_with_measure(self):
        mvs = MeasureValue.objects.by_regional_team([], measure_ids=['cerazette'])
        self.assertEqual(len(mvs), 2)

        mvs = MeasureValue.objects.by_regional_team([], measure_ids=['bananas'])
        self.assertEqual(len(mvs), 0)

    def test_by_regional_team_with_tag(self):
        mvs = MeasureValue.objects.by_regional_team([], tags=['core'])
        self.assertEqual(len(mvs), 2)

        mvs = MeasureValue.objects.by_regional_team([], tags=['lowpriority'])
        self.assertEqual(len(mvs), 0)

    def test_by_regional_team_with_tags(self):
        mvs = MeasureValue.objects.by_regional_team([], tags=['core', 'lowpriority'])
        self.assertEqual(len(mvs), 0)

    def test_by_stp_with_no_org(self):
        mvs = MeasureValue.objects.by_stp([])
        self.assertEqual(len(mvs), 2)

    def test_by_stp_with_org(self):
        mvs = MeasureValue.objects.by_stp(['E00000001'])
        self.assertEqual(len(mvs), 1)

    def test_by_stp_with_orgs(self):
        mvs = MeasureValue.objects.by_stp(['E00000001', 'E00000002'])
        self.assertEqual(len(mvs), 2)

    def test_by_stp_with_measure(self):
        mvs = MeasureValue.objects.by_stp([], measure_ids=['cerazette'])
        self.assertEqual(len(mvs), 2)

        mvs = MeasureValue.objects.by_stp([], measure_ids=['bananas'])
        self.assertEqual(len(mvs), 0)

    def test_by_stp_with_tag(self):
        mvs = MeasureValue.objects.by_stp([], tags=['core'])
        self.assertEqual(len(mvs), 2)

        mvs = MeasureValue.objects.by_stp([], tags=['lowpriority'])
        self.assertEqual(len(mvs), 0)

    def test_by_stp_with_tags(self):
        mvs = MeasureValue.objects.by_stp([], tags=['core', 'lowpriority'])
        self.assertEqual(len(mvs), 0)

    def test_by_ccg_with_no_org(self):
        mvs = MeasureValue.objects.by_ccg([])
        self.assertEqual(len(mvs), 2)

    def test_by_ccg_with_org(self):
        mvs = MeasureValue.objects.by_ccg(['04D'])
        self.assertEqual(len(mvs), 1)

    def test_by_ccg_with_orgs(self):
        mvs = MeasureValue.objects.by_ccg(['04D', '02Q'])
        self.assertEqual(len(mvs), 2)

    def test_by_ccg_with_measure(self):
        mvs = MeasureValue.objects.by_ccg([], measure_ids=['cerazette'])
        self.assertEqual(len(mvs), 2)

        mvs = MeasureValue.objects.by_ccg([], measure_ids=['bananas'])
        self.assertEqual(len(mvs), 0)

    def test_by_ccg_with_tag(self):
        mvs = MeasureValue.objects.by_ccg([], tags=['core'])
        self.assertEqual(len(mvs), 2)

        mvs = MeasureValue.objects.by_ccg([], tags=['lowpriority'])
        self.assertEqual(len(mvs), 0)

    def test_by_ccg_with_tags(self):
        mvs = MeasureValue.objects.by_ccg([], tags=['core', 'lowpriority'])
        self.assertEqual(len(mvs), 0)

    def test_by_practice_with_no_org(self):
        mvs = MeasureValue.objects.by_practice([])
        self.assertEqual(len(mvs), 10)

    def test_by_practice_with_pct_org(self):
        mvs = MeasureValue.objects.by_practice(['04D'])
        self.assertEqual(len(mvs), 1)

    def test_by_practice_with_practice_org(self):
        mvs = MeasureValue.objects.by_practice(['C83051'])
        self.assertEqual(len(mvs), 1)

    def test_by_practice_with_practice_orgs(self):
        mvs = MeasureValue.objects.by_practice(['C83051', 'C83019'])
        self.assertEqual(len(mvs), 2)

    def test_by_practice_with_measure(self):
        mvs = MeasureValue.objects.by_practice(
            ['C83051'], measure_ids=['cerazette'])
        self.assertEqual(len(mvs), 1)

        mvs = MeasureValue.objects.by_practice(
            ['C83051'], measure_ids=['bananas'])
        self.assertEqual(len(mvs), 0)

    def test_by_practice_with_tag(self):
        mvs = MeasureValue.objects.by_practice(['C83051'], tags=['core'])
        self.assertEqual(len(mvs), 1)

        mvs = MeasureValue.objects.by_practice(
            ['C83051'], tags=['lowpriority'])
        self.assertEqual(len(mvs), 0)

    def test_by_practice_with_tags(self):
        mvs = MeasureValue.objects.by_practice(
            ['C83051'], tags=['core', 'lowpriority'])
        self.assertEqual(len(mvs), 0)

    def test_aggregate_by_measure_and_month(self):
        results = (
            MeasureValue.objects
            .filter(measure_id='cerazette')
            .by_practice([])
            .aggregate_by_measure_and_month()
        )
        results = list(results)
        self.assertEqual(len(results), 1)
        mv = results[0]
        self.assertEqual(mv.measure_id, 'cerazette')
        self.assertEqual(mv.month, datetime.date(2015, 9, 1))
        self.assertEqual(mv.numerator, 85500)
        self.assertEqual(mv.denominator, 181500)
        self.assertEqual("%.4f" % mv.calc_value, '0.4711')
        self.assertEqual("%.2f" % mv.cost_savings['10'], '70149.77')
        self.assertEqual("%.2f" % mv.cost_savings['50'], '59029.41')
        self.assertEqual("%.2f" % mv.cost_savings['90'], '162.00')


class CalculateCostSavingsTests(TestCase):
    fixtures = ['lowpriority_measures']

    def test_calculate_cost_savings(self):
        measure_id = 'lpglucosamine'
        month = '2017-10-01'
        target_costs = (
            MeasureGlobal.objects
            .filter(measure_id=measure_id, month=month)
            .get()
            .percentiles['ccg']
        )
        cost_savings = (
            MeasureValue.objects
            .filter(measure_id=measure_id, month=month)
            .filter(practice_id__isnull=True)
            .calculate_cost_savings(target_costs)
        )
        self.assertEqual("%.2f" % cost_savings['10'], '516.88')
        self.assertEqual("%.2f" % cost_savings['50'], '401.60')
