from django.test import TestCase

from frontend.models import MeasureValue


class MeasureValueManagerTests(TestCase):
    fixtures = ['one_month_of_measures']

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

    def test_by_practice_with_orgs(self):
        mvs = MeasureValue.objects.by_practice(['C83051', '02Q'])
        self.assertEqual(len(mvs), 9)

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
