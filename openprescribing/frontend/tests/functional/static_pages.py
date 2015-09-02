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

    def test_bnf_chapter_page(self):
        url = 'http://localhost:8000/bnf/02'
        self.browser.get(url)

        all_spending_title = self.browser.find_element_by_css_selector('#all-spending .highcharts-title')
        self.assertEqual("Total spending by month", all_spending_title.text)
        detailed_spending_title = self.browser.find_element_by_css_selector('#detailed-spending .highcharts-title')
        self.assertEqual("Spending by chemical by month", detailed_spending_title.text)

    def test_bnf_section_page(self):
        url = 'http://localhost:8000/bnf/0202'
        self.browser.get(url)

        all_spending_title = self.browser.find_element_by_css_selector('#all-spending .highcharts-title')
        self.assertEqual("Total spending by month", all_spending_title.text)
        detailed_spending_title = self.browser.find_element_by_css_selector('#detailed-spending .highcharts-title')
        self.assertEqual("Spending by chemical by month", detailed_spending_title.text)

    def test_bnf_para_page(self):
        url = 'http://localhost:8000/bnf/020201'
        self.browser.get(url)

        all_spending_title = self.browser.find_element_by_css_selector('#all-spending .highcharts-title')
        self.assertEqual("Total spending by month", all_spending_title.text)
        detailed_spending_title = self.browser.find_element_by_css_selector('#detailed-spending .highcharts-title')
        self.assertEqual("Spending by chemical by month", detailed_spending_title.text)

    def test_chemical_page(self):
        url = 'http://localhost:8000/chemical/0202010D0'
        self.browser.get(url)

        all_spending_title = self.browser.find_element_by_css_selector('#all-spending .highcharts-title')
        self.assertEqual("Total spending by month", all_spending_title.text)
        detailed_spending_title = self.browser.find_element_by_css_selector('#detailed-spending .highcharts-title')
        self.assertEqual("Spending by presentation by month", detailed_spending_title.text)

    def test_practice_page(self):
        url = 'http://localhost:8000/practice/P87629'
        self.browser.get(url)

        all_spending_title = self.browser.find_element_by_css_selector('#all-spending .highcharts-title')
        self.assertEqual("Total spending by month", all_spending_title.text)

    def test_ccg_page(self):
        url = 'http://localhost:8000/ccg/06F'
        self.browser.get(url)

        map_panel = self.browser.find_elements_by_css_selector('#map .leaflet-clickable')
        self.assertEqual(len(map_panel), 1)

if __name__ == '__main__':
    unittest.main()
