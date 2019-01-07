# coding=utf8

# The tests in this file verify that the measure panels are generated as
# expected on each of the pages they appear on.  This is done by checking that
# the links on the panels point to the expected places, and that the perfomance
# explanations are correct.  The rendering of the measure graphs is not tested
# here.

from collections import defaultdict

from django.contrib.humanize.templatetags.humanize import intcomma
import requests
from selenium_base import SeleniumTestCase

from frontend.models import PCT, Practice, Measure, MeasureValue


class MeasuresTests(SeleniumTestCase):
    maxDiff = None

    fixtures = ['functional-measures']

    def _get(self, path):
        url = self.live_server_url + path
        rsp = requests.get(url)
        rsp.raise_for_status()
        self.browser.get(url)

    def _verify_link(self, panel_element, css_selector, exp_text, exp_path):
        element = panel_element.find_element_by_css_selector(css_selector)
        a_element = element.find_element_by_tag_name('a')
        self.assertEqual(a_element.text, exp_text)
        if exp_path is None:
            self.assertEqual(a_element.get_attribute('href'), '')
        else:
            self.assertEqual(a_element.get_attribute('href'), self.live_server_url + exp_path)

    def _find_measure_panel(self, id_):
        return self.find_by_css('#{} .panel'.format(id_))

    def test_all_england(self):
        self._get('/all-england/')

        panel_element = self._find_measure_panel('measure_lpzomnibus')
        self._verify_link(
            panel_element,
            '.inner li:nth-child(1)',
            'Break it down into its constituent measures.',
            None  # TODO fix this, it's a nothing link!
        )
        self._verify_link(
            panel_element,
            '.inner li:nth-child(2)',
            'Compare all CCGs in England on this measure',
            '/measure/lpzomnibus'
        )

        panel_element = self._find_measure_panel('measure_core_0')
        self._verify_link(
            panel_element,
            '.inner li:nth-child(1)',
            'Compare all CCGs in England on this measure',
            '/measure/core_0'
        )

    def test_all_england_low_priority(self):
        self._get('/all-england/?tags=lowpriority')

        panel_element = self._find_measure_panel('measure_lp_2')
        self._verify_link(
            panel_element,
            '.inner li:nth-child(1)',
            'Compare all CCGs in England on this measure',
            '/measure/lp_2'
        )

    def test_practice_home_page(self):
        self._get('/practice/P00000/')

        practice = Practice.objects.get(code='P00000')
        mvs = MeasureValue.objects.filter(practice=practice)
        extreme_measure = _get_extreme_measure(mvs)

        panel_element = self._find_measure_panel('top-measure-container')
        self._verify_link(
            panel_element,
            '.panel-heading',
            extreme_measure.name,
            '/ccg/AAA/{}'.format(extreme_measure.id)
        )

        panel_element = self._find_measure_panel('lpzomnibus-container')
        self._verify_link(
            panel_element,
            '.panel-heading',
            'LP omnibus measure',
            '/ccg/AAA/lpzomnibus'
        )

    def test_ccg_home_page(self):
        self._get('/ccg/AAA/')

        ccg = PCT.objects.get(code='AAA')
        mvs = MeasureValue.objects.filter(pct=ccg, practice=None)
        extreme_measure = _get_extreme_measure(mvs)

        panel_element = self._find_measure_panel('top-measure-container')
        self._verify_link(
            panel_element,
            '.panel-heading',
            extreme_measure.name,
            '/ccg/AAA/{}'.format(extreme_measure.id)
        )

        panel_element = self._find_measure_panel('lpzomnibus-container')
        self._verify_link(
            panel_element,
            '.panel-heading',
            'LP omnibus measure',
            '/ccg/AAA/lpzomnibus'
        )

    def test_measures_for_one_practice(self):
        self._get('/practice/P00000/measures/')

        panel_element = self._find_measure_panel('measure_core_0')
        self._verify_link(
            panel_element,
            '.panel-heading',
            'Core measure 0',
            '/ccg/AAA/core_0'
        )
        self._verify_link(
            panel_element,
            '.inner li:nth-child(1)',
            'Break the overall score down into individual presentations',
            '/measure/core_0/practice/P00000/'
        )
        self._verify_link(
            panel_element,
            '.inner li:nth-child(2)',
            'Compare all CCGs in England on this measure',
            '/measure/core_0'
        )

        panel_element = self._find_measure_panel('measure_lpzomnibus')
        self._verify_link(
            panel_element,
            '.panel-heading',
            'LP omnibus measure',
            '/ccg/AAA/lpzomnibus'
        )
        self._verify_link(
            panel_element,
            '.inner li:nth-child(1)',
            'Break it down into its constituent measures.',
            '/practice/P00000/measures/?tags=lowpriority'
        )
        self._verify_link(
            panel_element,
            '.inner li:nth-child(2)',
            'Break the overall score down into individual presentations',
            '/measure/lpzomnibus/practice/P00000/'
        )
        self._verify_link(
            panel_element,
            '.inner li:nth-child(3)',
            'Compare all CCGs in England on this measure',
            '/measure/lpzomnibus'
        )

    def test_measures_for_one_practice_low_priority(self):
        self._get('/practice/P00000/measures/?tags=lowpriority')

        panel_element = self._find_measure_panel('measure_lp_2')
        self._verify_link(
            panel_element,
            '.panel-heading',
            'LP measure 2',
            '/ccg/AAA/lp_2'
        )
        self._verify_link(
            panel_element,
            '.inner li:nth-child(1)',
            'Break the overall score down into individual presentations',
            '/measure/lp_2/practice/P00000/'
        )
        self._verify_link(
            panel_element,
            '.inner li:nth-child(2)',
            'Compare all CCGs in England on this measure',
            '/measure/lp_2'
        )

    def test_measures_for_one_ccg(self):
        self._get('/ccg/AAA/measures/')

        panel_element = self._find_measure_panel('measure_core_0')
        self._verify_link(
            panel_element,
            '.panel-heading',
            'Core measure 0',
            '/ccg/AAA/core_0'
        )
        self._verify_link(
            panel_element,
            '.inner li:nth-child(1)',
            'Break the overall score down into individual presentations',
            '/measure/core_0/ccg/AAA/'
        )
        self._verify_link(
            panel_element,
            '.inner li:nth-child(2)',
            'Split the measure into charts for individual practices',
            '/ccg/AAA/core_0'
        )
        self._verify_link(
            panel_element,
            '.inner li:nth-child(3)',
            'Compare all CCGs in England on this measure',
            '/measure/core_0'
        )

        panel_element = self._find_measure_panel('measure_lpzomnibus')
        self._verify_link(
            panel_element,
            '.panel-heading',
            'LP omnibus measure',
            '/ccg/AAA/lpzomnibus'
        )
        self._verify_link(
            panel_element,
            '.inner li:nth-child(1)',
            'Break it down into its constituent measures.',
            '/ccg/AAA/measures/?tags=lowpriority'
        )
        self._verify_link(
            panel_element,
            '.inner li:nth-child(2)',
            'Break the overall score down into individual presentations',
            '/measure/lpzomnibus/ccg/AAA/'
        )
        self._verify_link(
            panel_element,
            '.inner li:nth-child(3)',
            'Split the measure into charts for individual practices',
            '/ccg/AAA/lpzomnibus'
        )
        self._verify_link(
            panel_element,
            '.inner li:nth-child(4)',
            'Compare all CCGs in England on this measure',
            '/measure/lpzomnibus'
        )

    def test_measures_for_one_ccg_low_priority(self):
        self._get('/ccg/AAA/measures/?tags=lowpriority')

        panel_element = self._find_measure_panel('measure_lp_2')
        self._verify_link(
            panel_element,
            '.panel-heading',
            'LP measure 2',
            '/ccg/AAA/lp_2'
        )
        self._verify_link(
            panel_element,
            '.inner li:nth-child(1)',
            'Break the overall score down into individual presentations',
            '/measure/lp_2/ccg/AAA/'
        )
        self._verify_link(
            panel_element,
            '.inner li:nth-child(2)',
            'Split the measure into charts for individual practices',
            '/ccg/AAA/lp_2'
        )
        self._verify_link(
            panel_element,
            '.inner li:nth-child(3)',
            'Compare all CCGs in England on this measure',
            '/measure/lp_2'
        )

    def test_measure_for_all_ccgs(self):
        self._get('/measure/core_0/')

        panel_element = self._find_measure_panel('ccg_AAA')
        self._verify_link(
            panel_element,
            '.panel-heading',
            'AAA: CCG 0/0/0',
            '/ccg/AAA/measures/'
        )
        self._verify_link(
            panel_element,
            '.explanation li:nth-child(1)',
            'Split the measure into charts for individual practices',
            '/ccg/AAA/core_0'
        )
        self._verify_link(
            panel_element,
            '.explanation li:nth-child(2)',
            'Break the overall score down into individual presentations',
            '/measure/core_0/ccg/AAA/'
        )

    def test_measure_for_all_ccgs_with_tags_focus(self):
        self._get('/measure/lpzomnibus/')

        panel_element = self._find_measure_panel('ccg_AAA')
        self._verify_link(
            panel_element,
            '.panel-heading',
            'AAA: CCG 0/0/0',
            '/ccg/AAA/measures/'
        )
        self._verify_link(
            panel_element,
            '.explanation li:nth-child(1)',
            'Split the measure into charts for individual practices',
            '/ccg/AAA/lpzomnibus'
        )
        self._verify_link(
            panel_element,
            '.explanation li:nth-child(2)',
            'Break it down into its constituent measures',
            '/ccg/AAA/measures/?tags=lowpriority'
        )
        self._verify_link(
            panel_element,
            '.explanation li:nth-child(3)',
            'Break the overall score down into individual presentations',
            '/measure/lpzomnibus/ccg/AAA/'
        )

    def test_measure_for_one_practice(self):
        self._get('/measure/lp_2/practice/P00000/')

        panel_element = self._find_measure_panel('measure_lp_2')
        self._verify_link(
            panel_element,
            '.panel-heading',
            'LP measure 2',
            '/ccg/AAA/lp_2'
        )
        self._verify_link(
            panel_element,
            '.inner li:nth-child(1)',
            'Compare all CCGs in England on this measure',
            '/measure/lp_2'
        )

    def test_measure_for_one_ccg(self):
        self._get('/measure/lp_2/ccg/AAA/')

        panel_element = self._find_measure_panel('measure_lp_2')
        self._verify_link(
            panel_element,
            '.panel-heading',
            'LP measure 2',
            '/ccg/AAA/lp_2'
        )
        self._verify_link(
            panel_element,
            '.inner li:nth-child(1)',
            'Split the measure into charts for individual practices',
            '/ccg/AAA/lp_2'
        )
        self._verify_link(
            panel_element,
            '.inner li:nth-child(2)',
            'Compare all CCGs in England on this measure',
            '/measure/lp_2'
        )

    def test_measure_for_practices_in_ccg(self):
        self._get('/ccg/AAA/lp_2/')

        panel_element = self._find_measure_panel('practice_P00000')
        self._verify_link(
            panel_element,
            '.panel-heading',
            'P00000: Practice 0/0/0/0',
            '/practice/P00000/measures/'
        )
        self._verify_link(
            panel_element,
            '.explanation li:nth-child(1)',
            'Break the overall score down into individual presentations',
            '/measure/lp_2/practice/P00000/'
        )

    def test_explanation_for_all_england(self):
        mvs = MeasureValue.objects.filter(
            pct__isnull=False,
            practice__isnull=True,
            measure_id='core_0',
            month__gte='2018-03-01',
        )

        cost_saving_10 = sum(mv.cost_savings['10'] for mv in mvs if mv.cost_savings['10'] > 0)
        cost_saving_50 = sum(mv.cost_savings['50'] for mv in mvs if mv.cost_savings['50'] > 0)

        self._get('/all-england/')
        perf_element = self.find_by_xpath("//*[@id='measure_core_0']//strong[text()='Performance:']/..")
        exp_text = u'Performance: If all CCGs in England had prescribed in line with the median, the NHS would have spent £{} less over the past 6 months. If they had prescribed in line with the best 10%, it would have spent £{} less.'.format(_humanize(cost_saving_50), _humanize(cost_saving_10))
        self.assertEqual(perf_element.text, exp_text)

    def test_explanation_for_practice(self):
        # This test verifies that the explanation for a practice's performance
        # for a single measure is correct on each page where it appears.

        # First, we need to find interesting practices.  We want one that is
        # better than the 10th percentile, one that is between the 10th and
        # 50th percentiles, and one that is worse thanthe 50th percentiles.
        pp = []

        for p in Practice.objects.all():
            mvs = MeasureValue.objects.filter(
                practice=p,
                measure_id='core_0',
                month__gte='2018-03-01',
            )

            p.cost_saving_10 = sum(mv.cost_savings['10'] for mv in mvs)
            p.cost_saving_50 = sum(mv.cost_savings['50'] for mv in mvs)

            pp.append(p)

        # If the numerator items cost less than the denominator-only items,
        # then we can end up with a practice that is better than the 10th
        # percentile and worse than the 50th.  This makes no sense, and never
        # happens with production data.
        assert [p for p in pp if p.cost_saving_10 < 0 and p.cost_saving_50 > 0] == []

        # p1 is better than the 10th percentile
        # p2 is between the 10th and 50th percentiles
        # p3 is worse than the 50th percentile
        p1 = [p for p in pp if p.cost_saving_10 < 0 and p.cost_saving_50 < 0][0]
        p2 = [p for p in pp if p.cost_saving_10 > 0 and p.cost_saving_50 < 0][0]
        p3 = [p for p in pp if p.cost_saving_10 > 0 and p.cost_saving_50 > 0][0]

        p1_exp_text = u'By prescribing better than the median, this practice has saved the NHS £{} over the past 6 months.'.format(_humanize(p1.cost_saving_50))
        p2_exp_text = u'By prescribing better than the median, this practice has saved the NHS £{} over the past 6 months. If it had prescribed in line with the best 10%, it would have spent £{} less.'.format(_humanize(p2.cost_saving_50), _humanize(p2.cost_saving_10))
        p3_exp_text = u'If it had prescribed in line with the median, this practice would have spent £{} less over the past 6 months. If it had prescribed in line with the best 10%, it would have spent £{} less.'.format(_humanize(p3.cost_saving_50), _humanize(p3.cost_saving_10))

        # measure_for_one_practice
        self._get('/measure/core_0/practice/{}/'.format(p1.code))
        perf_element = self.find_by_xpath("//*[@id='measure_core_0']//strong[text()='Performance:']/..")
        self.assertIn(p1_exp_text, perf_element.text)

        self._get('/measure/core_0/practice/{}/'.format(p2.code))
        perf_element = self.find_by_xpath("//*[@id='measure_core_0']//strong[text()='Performance:']/..")
        self.assertIn(p2_exp_text, perf_element.text)

        self._get('/measure/core_0/practice/{}/'.format(p3.code))
        perf_element = self.find_by_xpath("//*[@id='measure_core_0']//strong[text()='Performance:']/..")
        self.assertIn(p3_exp_text, perf_element.text)

        # measures_for_one_practice
        self._get('/practice/{}/measures/'.format(p1.code))
        perf_element = self.find_by_xpath("//*[@id='measure_core_0']//strong[text()='Performance:']/..")
        self.assertIn(p1_exp_text, perf_element.text)

        # measure_for_practices_in_ccg
        ccg = p1.ccg
        self._get('/ccg/{}/core_0/'.format(ccg.code))
        panel_element = self._find_measure_panel('practice_{}'.format(p1.code))
        perf_element = panel_element.find_element_by_class_name('explanation')
        self.assertIn(p1_exp_text, perf_element.text)

        # practice_home_page
        self._get('/practice/{}/'.format(p1.code))
        panel_element = self._find_measure_panel('top-measure-container')
        perf_element = panel_element.find_element_by_class_name('explanation')
        self.assertIn(p1_exp_text, perf_element.text)

    def test_explanation_for_ccg(self):
        # See comments in test_explanation_for_practice for details.
        cc = []

        for c in PCT.objects.all():
            mvs = MeasureValue.objects.filter(
                pct=c,
                practice=None,
                measure_id='core_0',
                month__gte='2018-03-01',
            )

            c.cost_saving_10 = sum(mv.cost_savings['10'] for mv in mvs)
            c.cost_saving_50 = sum(mv.cost_savings['50'] for mv in mvs)

            cc.append(c)

        assert [c for c in cc if c.cost_saving_10 < 0 and c.cost_saving_50 > 0] == []
        c1 = [c for c in cc if c.cost_saving_10 < 0 and c.cost_saving_50 < 0][0]
        c2 = [c for c in cc if c.cost_saving_10 > 0 and c.cost_saving_50 < 0][0]
        c3 = [c for c in cc if c.cost_saving_10 > 0 and c.cost_saving_50 > 0][0]

        c1_exp_text = u'By prescribing better than the median, this CCG has saved the NHS £{} over the past 6 months.'.format(_humanize(c1.cost_saving_50))
        c2_exp_text = u'By prescribing better than the median, this CCG has saved the NHS £{} over the past 6 months. If it had prescribed in line with the best 10%, it would have spent £{} less.'.format(_humanize(c2.cost_saving_50), _humanize(c2.cost_saving_10))
        c3_exp_text = u'If it had prescribed in line with the median, this CCG would have spent £{} less over the past 6 months. If it had prescribed in line with the best 10%, it would have spent £{} less.'.format(_humanize(c3.cost_saving_50), _humanize(c3.cost_saving_10))

        # measure_for_one_ccg
        self._get('/measure/core_0/ccg/{}/'.format(c1.code))
        perf_element = self.find_by_xpath("//*[@id='measure_core_0']//strong[text()='Performance:']/..")
        self.assertIn(c1_exp_text, perf_element.text)

        self._get('/measure/core_0/ccg/{}/'.format(c2.code))
        perf_element = self.find_by_xpath("//*[@id='measure_core_0']//strong[text()='Performance:']/..")
        self.assertIn(c2_exp_text, perf_element.text)

        self._get('/measure/core_0/ccg/{}/'.format(c3.code))
        perf_element = self.find_by_xpath("//*[@id='measure_core_0']//strong[text()='Performance:']/..")
        self.assertIn(c3_exp_text, perf_element.text)

        # measures_for_one_ccg
        self._get('/ccg/{}/measures/'.format(c1.code))
        perf_element = self.find_by_xpath("//*[@id='measure_core_0']//strong[text()='Performance:']/..")
        self.assertIn(c1_exp_text, perf_element.text)

        # measure_for_all_ccgs
        self._get('/measure/core_0/')
        panel_element = self._find_measure_panel('ccg_{}'.format(c1.code))
        perf_element = panel_element.find_element_by_class_name('explanation')
        self.assertIn(c1_exp_text, perf_element.text)

        # ccg_home_page
        self._get('/ccg/{}/'.format(c1.code))
        panel_element = self._find_measure_panel('top-measure-container')
        perf_element = panel_element.find_element_by_class_name('explanation')
        self.assertIn(c1_exp_text, perf_element.text)

    def test_performance_summary_for_measure_for_all_ccgs(self):
        cost_saving = 0
        for c in PCT.objects.all():
            mvs = MeasureValue.objects.filter(
                pct=c,
                practice=None,
                measure_id='core_0',
                month__gte='2018-03-01',
            )
            ccg_cost_saving = sum(mv.cost_savings['50'] for mv in mvs)
            if ccg_cost_saving > 0:
                cost_saving += ccg_cost_saving

        self._get('/measure/core_0/')
        perf_summary_element = self.find_by_css('#perfsummary')
        exp_text = u'Over the past 6 months, if all CCGs had prescribed at the median ratio or better, then NHS England would have spent £{} less.'.format(_humanize(cost_saving))
        self.assertIn(exp_text, perf_summary_element.text)

    def test_performance_summary_for_measure_for_practices_in_ccg(self):
        # First we need to find a CCG with a cost saving!  In reality, almost
        # every CCG has a cost saving, but this is not the case with the test
        # data.

        for c in PCT.objects.all():
            cost_saving = 0

            for p in c.practice_set.all():
                mvs = MeasureValue.objects.filter(
                    practice=p,
                    measure_id='core_0',
                    month__gte='2018-03-01',
                )
                practice_cost_saving = sum(mv.cost_savings['50'] for mv in mvs)
                if practice_cost_saving > 0:
                    cost_saving += practice_cost_saving

            if cost_saving > 0:
                break
        else:
            assert False, 'Could not find CCG with cost saving!'

        self._get('/ccg/{}/core_0/'.format(c.code))
        perf_summary_element = self.find_by_css('#perfsummary')
        exp_text = u'Over the past 6 months, if all practices had prescribed at the median ratio or better, then this CCG would have spent £{} less.'.format(_humanize(cost_saving))
        self.assertIn(exp_text, perf_summary_element.text)

    def test_performance_summary_for_measures_for_one_ccg(self):
        # First we need to find a CCG with a cost saving!  In reality, almost
        # every CCG has a cost saving, but this is not the case with the test
        # data.

        for c in PCT.objects.all():
            mvs = MeasureValue.objects.filter(
                pct=c,
                practice=None,
                measure_id__in=['core_0', 'core_1', 'lpzomnibus'],
                month__gte='2018-03-01',
            )
            cost_saving = sum(mv.cost_savings['50'] for mv in mvs)
            if cost_saving > 0:
                break
        else:
            assert False, 'Could not find CCG with cost saving!'

        self._get('/ccg/{}/measures/'.format(c.code))
        perf_summary_element = self.find_by_css('#perfsummary')
        exp_text = u'Over the past 6 months, if this CCG had prescribed at the median ratio or better on all cost-saving measures below, then it would have spent £{} less.'.format(_humanize(cost_saving))
        self.assertIn(exp_text, perf_summary_element.text)

    def test_performance_summary_for_measures_for_one_practice(self):
        # First we need to find a practice with a cost saving!  In reality,
        # almost every practice has a cost saving, but this is not the case
        # with the test data.

        for p in Practice.objects.all():
            mvs = MeasureValue.objects.filter(
                practice=p,
                measure_id__in=['core_0', 'core_1', 'lpzomnibus'],
                month__gte='2018-03-01',
            )
            cost_saving = sum(mv.cost_savings['50'] for mv in mvs)
            if cost_saving > 0:
                break
        else:
            assert False, 'Could not find practice with cost saving!'

        self._get('/practice/{}/measures/'.format(p.code))
        perf_summary_element = self.find_by_css('#perfsummary')
        exp_text = u'Over the past 6 months, if this practice had prescribed at the median ratio or better on all cost-saving measures below, then it would have spent £{} less.'.format(_humanize(cost_saving))
        self.assertIn(exp_text, perf_summary_element.text)


def _humanize(cost_saving):
    return intcomma(int(round(abs(cost_saving))))


def _get_extreme_measure(mvs):
    mvs = mvs.filter(month__gte='2018-03-01', measure_id__in=['core_0', 'core_1'])
    percentiles_by_measure_id = defaultdict(list)
    for mv in mvs:
        if mv.percentile is not None:
            percentiles_by_measure_id[mv.measure_id].append(mv.percentile)

    avg_percentile_by_measure_id = {
        measure_id: sum(percentiles) / len(percentiles)
        for measure_id, percentiles in percentiles_by_measure_id.items()
    }

    measure_id = max(avg_percentile_by_measure_id, key=avg_percentile_by_measure_id.get)

    return Measure.objects.get(id=measure_id)
