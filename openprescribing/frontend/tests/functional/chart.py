# -*- coding: UTF-8 -*-
from selenium import webdriver
from django.test import TestCase
import unittest


class FrontendTest(unittest.TestCase):

    def setUp(self):
        self.browser = webdriver.Firefox()
        self.browser.implicitly_wait(20)

    def tearDown(self):
        self.browser.quit()

    def test_chart_linear_log_scale_button_works(self):
        url = 'http://localhost:8000/analyse/'
        url += '#org=CCG&numerator=chemical&numeratorIds=0501013E0'
        url += '&denominator=chemical&denominatorIds=0501013B0'
        self.browser.get(url)

        xaxis_labels = self.browser.find_elements_by_css_selector('.highcharts-xaxis-labels text')
        yaxis_labels = self.browser.find_elements_by_css_selector('.highcharts-yaxis-labels text')
        self.assertEqual(xaxis_labels[-1].text, u'\xa3350k')
        self.assertEqual(yaxis_labels[-1].text, u'\xa33000')

        self.browser.find_element_by_css_selector('#log').click()
        xaxis_labels = self.browser.find_elements_by_css_selector('.highcharts-xaxis-labels text')
        yaxis_labels = self.browser.find_elements_by_css_selector('.highcharts-yaxis-labels text')
        self.assertEqual(xaxis_labels[-1].text, u'\xa31m')
        self.assertEqual(yaxis_labels[-1].text, u'\xa310k')

        self.browser.find_element_by_css_selector('#linear').click()
        xaxis_labels = self.browser.find_elements_by_css_selector('.highcharts-xaxis-labels text')
        yaxis_labels = self.browser.find_elements_by_css_selector('.highcharts-yaxis-labels text')
        self.assertEqual(xaxis_labels[-1].text, u'\xa3350k')
        self.assertEqual(yaxis_labels[-1].text, u'\xa33000')

    def test_chart_linear_log_scale_button_with_many_zeroes(self):
        url = 'http://localhost:8000/analyse/'
        url += '#org=practice&numerator=presentation&numeratorIds='
        url += '0212000AAAAAAAA&denominator=presentation&'
        url += 'denominatorIds=0212000B0AAACAC,0212000B0AAADAD&'
        url += 'scale=linear'
        self.browser.get(url)

        xaxis_labels = self.browser.find_elements_by_css_selector('.highcharts-xaxis-labels text')
        yaxis_labels = self.browser.find_elements_by_css_selector('.highcharts-yaxis-labels text')
        self.assertEqual(xaxis_labels[-1].text, u'\xa3350k')
        self.assertEqual(yaxis_labels[-1].text, u'\xa33000')

        self.browser.find_element_by_css_selector('#log').click()
        xaxis_labels = self.browser.find_elements_by_css_selector('.highcharts-xaxis-labels text')
        yaxis_labels = self.browser.find_elements_by_css_selector('.highcharts-yaxis-labels text')
        self.assertEqual(xaxis_labels[-1].text, u'\xa31m')
        self.assertEqual(yaxis_labels[-1].text, u'\xa310k')

        self.browser.find_element_by_css_selector('#linear').click()
        xaxis_labels = self.browser.find_elements_by_css_selector('.highcharts-xaxis-labels text')
        yaxis_labels = self.browser.find_elements_by_css_selector('.highcharts-yaxis-labels text')
        self.assertEqual(xaxis_labels[-1].text, u'\xa3350k')
        self.assertEqual(yaxis_labels[-1].text, u'\xa33000')

    def test_chart_autocomplete_and_highlight(self):
        url = 'http://localhost:8000/analyse/'
        url += '#org=CCG&numerator=chemical&numeratorIds=0501013E0'
        url += '&denominator=chemical&denominatorIds=0501013B0'
        self.browser.get(url)

        org = self.browser.find_element_by_css_selector('#findItem')
        org.send_keys("Stafford")
        suggestions = self.browser.find_elements_by_css_selector('#findItemWrapper .tt-suggestion')
        self.assertEqual(len(suggestions), 3)
        suggestions[0].click()

        tooltip = self.browser.find_element_by_css_selector('.highcharts-tooltip')
        tooltip_html = tooltip.get_attribute("innerHTML")
        self.assertIn("NHS East Staffordshire", tooltip_html)
        self.assertIn("Spend on 0501013E0:", tooltip_html)
        self.assertIn("Spend on 0501013B0:", tooltip_html)

    def test_chart_slider(self):
        url = 'http://localhost:8000/analyse/'
        url += '#org=CCG&numerator=chemical&numeratorIds=0501013E0'
        url += '&denominator=chemical&denominatorIds=0501013B0'
        self.browser.get(url)

        slider_checkbox = self.browser.find_element_by_css_selector('#enable-date')
        slider_checkbox.click()

        # TODO: Add stuff here

if __name__ == '__main__':
    unittest.main()
