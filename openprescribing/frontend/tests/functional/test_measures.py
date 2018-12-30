# The tests in this file verify that the measure panels are generated as
# expected on each of the pages they appear on.  This is done by checking that
# the links on the panels point to the expected places.  The rendering of the
# measure graphs is not tested here.

import requests
from selenium_base import SeleniumTestCase


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
        self.assertEqual(a_element.get_attribute('href'), self.live_server_url + exp_path)

    def _find_measure_panel(self, id_):
        return self.find_by_css('#{} .panel'.format(id_))

    def test_practice_home_page(self):
        self._get('/practice/P00000/')

        panel_element = self._find_measure_panel('top-measure-container')
        self._verify_link(
            panel_element,
            '.panel-heading',
            'Measure 2',
            '/ccg/AAA/measure_2'
        )

        panel_element = self._find_measure_panel('lpzomnibus-container')
        self._verify_link(
            panel_element,
            '.panel-heading',
            'Measure 0',
            '/ccg/AAA/lpzomnibus'
        )

    def test_ccg_home_page(self):
        self._get('/ccg/AAA/')

        panel_element = self._find_measure_panel('top-measure-container')
        self._verify_link(
            panel_element,
            '.panel-heading',
            'Measure 2',
            '/ccg/AAA/measure_2'
        )

        panel_element = self._find_measure_panel('lpzomnibus-container')
        self._verify_link(
            panel_element,
            '.panel-heading',
            'Measure 0',
            '/ccg/AAA/lpzomnibus'
        )

    def test_measures_for_one_practice(self):
        self._get('/practice/P00000/measures/')

        panel_element = self._find_measure_panel('measure_measure_2')
        self._verify_link(
            panel_element,
            '.panel-heading',
            'Measure 2',
            '/ccg/AAA/measure_2'
        )
        self._verify_link(
            panel_element,
            '.inner li:nth-child(1)',
            'Break the overall score down into individual presentations',
            '/measure/measure_2/practice/P00000/'
        )
        self._verify_link(
            panel_element,
            '.inner li:nth-child(2)',
            'Compare all CCGs in England on this measure',
            '/measure/measure_2'
        )

        panel_element = self._find_measure_panel('measure_lpzomnibus')
        self._verify_link(
            panel_element,
            '.panel-heading',
            'Measure 0',
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

        panel_element = self._find_measure_panel('measure_measure_1')
        self._verify_link(
            panel_element,
            '.panel-heading',
            'Measure 1',
            '/ccg/AAA/measure_1'
        )
        self._verify_link(
            panel_element,
            '.inner li:nth-child(1)',
            'Break the overall score down into individual presentations',
            '/measure/measure_1/practice/P00000/'
        )
        self._verify_link(
            panel_element,
            '.inner li:nth-child(2)',
            'Compare all CCGs in England on this measure',
            '/measure/measure_1'
        )

    def test_measures_for_one_ccg(self):
        self._get('/ccg/AAA/measures/')

        panel_element = self._find_measure_panel('measure_measure_2')
        self._verify_link(
            panel_element,
            '.panel-heading',
            'Measure 2',
            '/ccg/AAA/measure_2'
        )
        self._verify_link(
            panel_element,
            '.inner li:nth-child(1)',
            'Break the overall score down into individual presentations',
            '/measure/measure_2/ccg/AAA/'
        )
        self._verify_link(
            panel_element,
            '.inner li:nth-child(2)',
            'Split the measure into charts for individual practices',
            '/ccg/AAA/measure_2'
        )
        self._verify_link(
            panel_element,
            '.inner li:nth-child(3)',
            'Compare all CCGs in England on this measure',
            '/measure/measure_2'
        )

        panel_element = self._find_measure_panel('measure_lpzomnibus')
        self._verify_link(
            panel_element,
            '.panel-heading',
            'Measure 0',
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

        panel_element = self._find_measure_panel('measure_measure_1')
        self._verify_link(
            panel_element,
            '.panel-heading',
            'Measure 1',
            '/ccg/AAA/measure_1'
        )
        self._verify_link(
            panel_element,
            '.inner li:nth-child(1)',
            'Break the overall score down into individual presentations',
            '/measure/measure_1/ccg/AAA/'
        )
        self._verify_link(
            panel_element,
            '.inner li:nth-child(2)',
            'Split the measure into charts for individual practices',
            '/ccg/AAA/measure_1'
        )
        self._verify_link(
            panel_element,
            '.inner li:nth-child(3)',
            'Compare all CCGs in England on this measure',
            '/measure/measure_1'
        )

    def test_measure_for_all_ccgs(self):
        self._get('/measure/measure_2/')

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
            '/ccg/AAA/measure_2'
        )
        self._verify_link(
            panel_element,
            '.explanation li:nth-child(2)',
            'Break the overall score down into individual presentations',
            '/measure/measure_2/ccg/AAA/'
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
        self._get('/measure/measure_1/practice/P00000/')

        panel_element = self._find_measure_panel('measure_measure_1')
        self._verify_link(
            panel_element,
            '.panel-heading',
            'Measure 1',
            '/ccg/AAA/measure_1'
        )
        self._verify_link(
            panel_element,
            '.inner li:nth-child(1)',
            'Compare all CCGs in England on this measure',
            '/measure/measure_1'
        )

    def test_measure_for_one_ccg(self):
        self._get('/measure/measure_1/ccg/AAA/')

        panel_element = self._find_measure_panel('measure_measure_1')
        self._verify_link(
            panel_element,
            '.panel-heading',
            'Measure 1',
            '/ccg/AAA/measure_1'
        )
        self._verify_link(
            panel_element,
            '.inner li:nth-child(1)',
            'Split the measure into charts for individual practices',
            '/ccg/AAA/measure_1'
        )
        self._verify_link(
            panel_element,
            '.inner li:nth-child(2)',
            'Compare all CCGs in England on this measure',
            '/measure/measure_1'
        )

    def test_measure_for_practices_in_ccg(self):
        self._get('/ccg/AAA/measure_1/')

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
            '/measure/measure_1/practice/P00000/'
        )
