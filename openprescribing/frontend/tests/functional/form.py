# -*- coding: UTF-8 -*-
from selenium import webdriver
import unittest


class FrontendTest(unittest.TestCase):

    def setUp(self):
        self.browser = webdriver.Firefox()
        self.browser.implicitly_wait(20)

    def tearDown(self):
        self.browser.quit()

    def test_form_and_chart_render_from_url(self):
        url = 'http://localhost:8000/analyse/'
        url += '#org=practice&numerator=presentation&numeratorIds='
        url += '0212000AAAAAAAA&denominator=presentation&'
        url += 'denominatorIds=0212000B0AAACAC,0212000B0AAADAD&'
        url += 'period=all-time&scale=log'

        self.browser.get(url)
        self.assertIn('Analyse', self.browser.title)

        # Form <select> elements
        org = self.browser.find_element_by_id('org')
        self.assertEqual('practice', org.get_attribute("value"))
        num_type = self.browser.find_element_by_id('numerator')
        self.assertEqual('presentation', num_type.get_attribute("value"))
        denom_type = self.browser.find_element_by_id('denominator')
        self.assertEqual('presentation', denom_type.get_attribute("value"))

        # Form <input> elements
        num_val_css = '#numerator-row .tt-input'
        num_val = self.browser.find_element_by_css_selector(num_val_css)
        self.assertEqual('0212000AAAAAAAA', num_val.get_attribute("value"))
        denom_val_css = '#denominator-row .tt-input'
        denom_val = self.browser.find_elements_by_css_selector(denom_val_css)
        self.assertEqual('0212000B0AAACAC', denom_val[
                         0].get_attribute("value"))
        self.assertEqual('0212000B0AAADAD', denom_val[
                         1].get_attribute("value"))

        # Chart title, axis titles, axis labels
        title = self.browser.find_element_by_css_selector('.highcharts-title')
        expected_title = 'Total spending by practice on 0212000AAAAAAAA'
        expected_title += 'vs. spending on 0212000B0AAACAC + 0212000B0AAADAD '
        expected_title += 'since August 2010'
        self.assertEqual(expected_title, title.text)
        yaxis_css = '.highcharts-yaxis-title'
        yaxis_title = self.browser.find_element_by_css_selector(yaxis_css)
        self.assertEqual('Spend on 0212000AAAAAAAA', yaxis_title.text)
        xaxis_css = '.highcharts-xaxis-title'
        xaxis_title = self.browser.find_element_by_css_selector(xaxis_css)
        self.assertEqual(
            'Spend on 0212000B0AAACAC + 0212000B0AAADAD', xaxis_title.text)
        xaxis_labels = self.browser.find_elements_by_css_selector(
            '.highcharts-xaxis-labels text')
        self.assertEqual(xaxis_labels[-1].text, u'\xa3100k')
        yaxis_labels = self.browser.find_elements_by_css_selector(
            '.highcharts-yaxis-labels text')
        self.assertEqual(yaxis_labels[-1].text, u'\xa31m')

        scale_button = self.browser.find_element_by_css_selector(
            '#useLogScale .btn-primary')
        self.assertEqual('Log scale', scale_button.text)
        update_button = self.browser.find_element_by_css_selector('#update')
        self.assertEqual(None, update_button.get_attribute("disabled"))

        chart_points = self.browser.find_elements_by_css_selector(
            '.highcharts-markers path')
        self.assertEqual(len(chart_points), 7894)

    def test_form_and_chart_render_from_url_with_list_size(self):
        '''
        TODO: Add test for CCG list size query.
        '''
        url = 'http://localhost:8000/analyse/'
        url += '#org=practice&numerator=chemical&numeratorIds='
        url += '0212000AA&denominator=list-size&'
        url += 'period=all-time&scale=linear'

        self.browser.get(url)

        # Form <select> elements
        org = self.browser.find_element_by_id('org')
        self.assertEqual('practice', org.get_attribute("value"))
        num_type = self.browser.find_element_by_id('numerator')
        self.assertEqual('chemical', num_type.get_attribute("value"))
        denom_type = self.browser.find_element_by_id('denominator')
        self.assertEqual('list-size', denom_type.get_attribute("value"))

        # Form <input> elements
        num_val_css = '#numerator-row .tt-input'
        num_val = self.browser.find_element_by_css_selector(num_val_css)
        self.assertEqual('0212000AA', num_val.get_attribute("value"))
        denom_val_css = '#denominator-row .tt-input'
        denom_val = self.browser.find_elements_by_css_selector(denom_val_css)
        self.assertEqual(0, len(denom_val))

        # Chart title, axis titles, axis labels
        title = self.browser.find_element_by_css_selector('.highcharts-title')
        expected_title = (
            'Total spending by practice on 0212000AA since August 2010')
        expected_title += 'vs. list size in 2013'
        self.assertEqual(expected_title, title.text)
        yaxis_css = '.highcharts-yaxis-title'
        yaxis_title = self.browser.find_element_by_css_selector(yaxis_css)
        self.assertEqual('Spend on 0212000AA', yaxis_title.text)
        xaxis_css = '.highcharts-xaxis-title'
        xaxis_title = self.browser.find_element_by_css_selector(xaxis_css)
        self.assertEqual('List size 2013', xaxis_title.text)
        xaxis_labels = self.browser.find_elements_by_css_selector(
            '.highcharts-xaxis-labels text')
        self.assertEqual(xaxis_labels[-1].text, u'60k')
        yaxis_labels = self.browser.find_elements_by_css_selector(
            '.highcharts-yaxis-labels text')
        self.assertEqual(yaxis_labels[-1].text, u'\xa3125k')

        scale_button = self.browser.find_element_by_css_selector(
            '#useLogScale .btn-primary')
        self.assertEqual('Linear scale', scale_button.text)
        update_button = self.browser.find_element_by_css_selector('#update')
        self.assertEqual(None, update_button.get_attribute("disabled"))

        chart_points = self.browser.find_elements_by_css_selector(
            '.highcharts-markers path')
        self.assertEqual(len(chart_points), 11864)

    def test_chart_does_not_prerender_from_incomplete_url(self):
        url = 'http://localhost:8000/analyse/#org=CCG'
        url += '&numerator=bnf-section&numeratorIds=030401'
        self.browser.get(url)

        # Form <select> elements
        org = self.browser.find_element_by_id('org')
        self.assertEqual('CCG', org.get_attribute("value"))
        num_type = self.browser.find_element_by_id('numerator')
        self.assertEqual('bnf-section', num_type.get_attribute("value"))
        denom_type = self.browser.find_element_by_id('denominator')
        self.assertEqual('chemical', denom_type.get_attribute("value"))

        # Form <input> elements
        num_val_css = '#numerator-row .tt-input'
        num_val = self.browser.find_element_by_css_selector(num_val_css)
        self.assertEqual('030401', num_val.get_attribute("value"))
        denom_val_css = '#denominator-row .tt-input'
        denom_val = self.browser.find_element_by_css_selector(denom_val_css)
        self.assertEqual('', denom_val.get_attribute("value"))

        # Chart
        chart = self.browser.find_element_by_css_selector('#chart')
        self.assertEqual('', chart.get_attribute('innerHTML'))
        update_button = self.browser.find_element_by_css_selector('#update')
        self.assertEqual('true', update_button.get_attribute("disabled"))

    def test_form_autocomplete(self):
        url = 'http://localhost:8000/analyse/#org=CCG'
        url += '&numerator=bnf-section&numeratorIds=030401'
        self.browser.get(url)

        num_type = self.browser.find_element_by_id('numerator')
        self.assertEqual('bnf-section', num_type.get_attribute("value"))
        num_val = self.browser.find_element_by_css_selector(
            '#numerator-row .tt-input')
        self.assertEqual('030401', num_val.get_attribute("value"))

        # Test BNF section autocomplete
        num_val.clear()
        num_val.send_keys("4.2")
        suggestions = self.browser.find_elements_by_css_selector(
            '#numerator-row .tt-suggestion')
        self.assertEqual(len(suggestions), 4)
        self.assertEqual(suggestions[1].text, 'Antipsychotic Drugs (4.2.1)')

        # Test presentation autocomplete
        num_chosen = self.browser.find_element_by_id('numerator_chosen')
        num_chosen.click()
        num_options = self.browser.find_elements_by_css_selector(
            '#numerator_chosen li')
        num_options[0].click()
        num_val = self.browser.find_element_by_css_selector(
            '#numerator-row .tt-input')
        num_val.click()
        num_val.send_keys("0501013B0")
        suggestions = self.browser.find_elements_by_css_selector(
            '#numerator-row .tt-suggestion')
        self.assertEqual(len(suggestions), 15)
        self.assertEqual(suggestions[0].text,
                         'Amoxicillin_Cap 250mg (0501013B0AAAAAA)')

        # Test chemical autocomplete
        denom_val_css = '#denominator-row .tt-input'
        denom_val = self.browser.find_element_by_css_selector(denom_val_css)
        denom_val.send_keys("0501013B0")
        suggestions = self.browser.find_elements_by_css_selector(
            '#denominator-row .tt-suggestion')
        self.assertEqual(len(suggestions), 1)
        self.assertEqual(suggestions[0].text, 'Amoxicillin (0501013B0)')

        # Test incorrect value
        denom_val.clear()
        denom_val.send_keys("xxx")
        denom_val.send_keys("xxx")
        suggestions = self.browser.find_elements_by_css_selector(
            '#denominator-row .tt-suggestion')
        self.assertEqual(len(suggestions), 0)

    def test_form_submit(self):
        '''
        Test that the chart renders when the form is submitted.
        '''
        url = 'http://localhost:8000/analyse'
        self.browser.get(url)

        num_val = self.browser.find_element_by_css_selector(
            '#numerator-row .tt-input')
        num_val.send_keys("0501013E0")
        suggestions = self.browser.find_elements_by_css_selector(
            '#numerator-row .tt-suggestion')
        suggestions[0].click()

        denom_val = self.browser.find_element_by_css_selector(
            '#denominator-row .tt-input')
        denom_val.send_keys("0501013B0")
        suggestions = self.browser.find_elements_by_css_selector(
            '#denominator-row .tt-suggestion')
        suggestions[0].click()

        update_button = self.browser.find_element_by_css_selector('#update')
        update_button.click()

        title = self.browser.find_element_by_css_selector('.highcharts-title')
        self.assertEqual(
            'Total spending by CCG on Ampicillin (0501013E0)vs. '
            'spending on Amoxicillin (0501013B0) since April 2013', title.text)

    def test_form_add_buttons(self):
        '''
        Test that a rendered chart interacts as we expect:
        - typing in the organisation box causes autocomplete
        - clicking on the linear/log button causes the chart to re-render
        '''
        url = 'http://localhost:8000/analyse/'
        url += '#org=CCG&numerator=chemical&numeratorIds=0501013E0'
        url += '&denominator=chemical&denominatorIds=0501013B0'
        self.browser.get(url)

        self.browser.find_element_by_css_selector(
            '#numerator-row .add').click()
        num_inputs = self.browser.find_elements_by_css_selector(
            '#numerator-row .tt-input')
        self.assertEqual(len(num_inputs), 2)
        self.assertEqual(num_inputs[0].get_attribute("value"), "0501013E0")
        self.assertEqual(num_inputs[1].get_attribute("value"), "")

        self.browser.find_element_by_css_selector(
            '#denominator-row .add').click()
        denom_inputs = self.browser.find_elements_by_css_selector(
            '#denominator-row .tt-input')
        self.assertEqual(len(denom_inputs), 2)
        self.assertEqual(denom_inputs[0].get_attribute("value"), "0501013B0")
        self.assertEqual(denom_inputs[1].get_attribute("value"), "")
        denom_inputs[1].send_keys("0501013A0")

        denom_minus = self.browser.find_elements_by_css_selector(
            '#denominator-row .minus')
        denom_minus[1].click()
        denom_inputs = self.browser.find_elements_by_css_selector(
            '#denominator-row .tt-input')
        self.assertEqual(len(denom_inputs), 1)
        self.assertEqual(denom_inputs[0].get_attribute("value"), "0501013B0")

if __name__ == '__main__':
    unittest.main()
