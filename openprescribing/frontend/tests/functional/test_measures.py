# The tests in this file verify that the measure panels are generated as
# expected on each of the pages they appear on.  This is done by checking that
# the links on the panels point to the expected places.  The rendering of the
# measure graphs is not tested here.

from collections import defaultdict

import requests
from selenium_base import SeleniumTestCase

from frontend.models import PCT, Practice, Measure, MeasureValue


class MeasuresTests(SeleniumTestCase):
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
