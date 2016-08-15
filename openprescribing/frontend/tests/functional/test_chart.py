# -*- coding: utf-8 -*-
import unittest
from django.core import management

from frontend.tests.test_api_measures import setUpModule as setUpMeasures
from selenium_base import SeleniumTestCase


class FrontendTest(SeleniumTestCase):

    def test_ccg_measures_sorting(self):
        # add CCGs and one measure
        setUpMeasures()

        # add another so we can sort
        month = '2015-09-01'
        measure_id = 'keppra'
        args = []
        opts = {
            'month': month,
            'measure': measure_id
        }
        management.call_command('import_measures', *args, **opts)

        url = self.live_server_url + '/ccg/02Q/measures/'
        self.browser.get(url)
        # The default should be sorting by percentile, then id
        self.assertEqual(self.browser.find_element_by_xpath(
            "//div[@id='charts']/div[1]").get_attribute("id"),
                         'measure_cerazette')

        # Now click to sort by potential savings
        self.browser.find_element_by_xpath(
            "//button[@data-orderby='savings']").click()

        # hack: not sure of the correct way to await the element
        # being visible.
        import time
        time.sleep(1)
        self.assertEqual(self.browser.find_element_by_xpath(
            "//div[@id='charts']/div[1]").get_attribute("id"),
                         'measure_keppra')

if __name__ == '__main__':
    unittest.main()
