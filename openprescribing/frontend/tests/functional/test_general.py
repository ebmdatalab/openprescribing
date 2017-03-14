# -*- coding: utf-8 -*-
import json
import unittest

from django.http import JsonResponse
from mock import patch
from mock import MagicMock
from mock import PropertyMock
from selenium_base import SeleniumTestCase


class MockApiBase(dict):
    """Mocks methods listed in `mock_methods` with functions that have
    corresponding names in the MockApi class.

    """

    def __init__(self):
        self.fixtures_base = 'frontend/tests/fixtures/functional/'
        for method in self.__class__.mock_methods:
            self[method] = MagicMock(side_effect=getattr(self, method))

    def _load_json(self, name):
        return json.load(open("%s/%s.json" % (self.fixtures_base, name), 'r'))


class MockSpendingApi(MockApiBase):
    mock_methods = ['spending_by_ccg']

    def spending_by_ccg(self, request):
        data = {}
        code = request.GET.get('code', '')
        if code == '2.12':
            data = self._load_json('spending_by_ccg_denom')
        elif code == '0212000AA':
            data = self._load_json('spending_by_ccg_num')
        return JsonResponse(data, status=200, safe=False)


class MockBnfApi(MockApiBase):
    mock_methods = ['bnf_codes']

    def bnf_codes(self, request):
        data = {}
        code = request.GET.get('q', '')
        if code.startswith('0212000AA'):
            data = self._load_json('bnf_code_num')
        elif code.startswith('2.12'):
            data = self._load_json('bnf_code_denom')
        return JsonResponse(data, status=200, safe=False)


class MockLocationApi(MockApiBase):
    mock_methods = ['org_location']

    def org_location(self, request):
        data = self._load_json('org_location_ccg')
        return JsonResponse(data, status=200, safe=False)


mock_spending_api = MockSpendingApi()
mock_bnf_api = MockBnfApi()
mock_location_api = MockLocationApi()


class MapTest(SeleniumTestCase):
    @patch.dict('api.views_spending.__dict__', mock_spending_api)
    @patch.dict('api.views_bnf_codes.__dict__', mock_bnf_api)
    @patch.dict('api.views_org_location.__dict__', mock_location_api)
    def test_map_slider(self):
        # Check that Gravesend has the expected popover by default
        self.browser.get(
            self.live_server_url +
            '/analyse/#org=CCG&numIds=0212000AA&denomIds=2.12&selectedTab=map')
        gravesend = self.find_by_xpath(
            "//*[@fill='#67001f' and name()='path']")
        gravesend.click()
        popup = self.find_by_xpath(
            "//*[contains(@class, 'leaflet-popup-content')]")
        self.assertTrue(popup.is_displayed())
        self.assertIn(
            "NHS DARTFORD, GRAVESHAM AND SWANLEY CCG\nItems for Rosuvastatin "
            "Calcium in Sep '16", popup.text)

        # Move the slider
        #
        # The firefox webdriver doesn't currently support mouse
        # events, so we have to inject them straight into the browser.
        js = """
        var slider = $('#chart-date-slider');
        slider.val(0);
        slider.trigger('change');
        """
        self.browser.execute_script(js)

        # Check the values for Gravesend have changed as expected
        gravesend = self.find_by_xpath(
            "//*[@fill='#ed9576' and name()='path']")
        gravesend.click()
        popup = self.find_by_xpath(
            "//*[contains(@class, 'leaflet-popup-content')]")
        self.assertIn(
            "NHS DARTFORD, GRAVESHAM AND SWANLEY CCG\nItems for Rosuvastatin "
            "Calcium in Apr '13", popup.text)
        self.assertTrue(popup.is_displayed())


class GeneralFrontendTest(SeleniumTestCase):
    fixtures = ['functional_test_data']

    def test_menu_dropdown_on_doc_page(self):
        with patch('requests.get') as mock_response:
            # Mock the text fetched from Google Docs
            text = PropertyMock(
                return_value=('<head><style></style></head>'
                              '<body>some text</body>'))
            type(mock_response.return_value).text = text
            url = self.live_server_url + '/docs/analyse/'
            self.browser.get(url)
            self.find_by_xpath("//a[contains(text(), 'More')]").click()
            self.assertTrue(
                self.find_by_xpath(
                    "//a[contains(text(), 'About')]").is_displayed(),
                "dropdown functionality broken at %s" % url
            )

    def test_menu_dropdown(self):
        for url in ['/ccg/03Q/',
                    '/practice/P87629/',
                    '/measure/cerazette/',
                    '/chemical/0202010D0/',
                    '/bnf/020201/',
                    '/analyse/',
                    '/about']:
            url = self.live_server_url + url
            self.browser.get(url)
            try:
                self.find_by_xpath("//a[contains(text(), 'More')]").click()
            except AssertionError as e:
                e.args += ("at URL %s" % url,)
                raise
            self.assertTrue(
                self.find_by_xpath(
                    "//a[contains(text(), 'About')]").is_displayed(),
                "dropdown functionality broken at %s" % url
            )

    def test_message_and_action(self):
        for url in ['/ccg/03Q/',
                    '/practice/P87629/',
                    '/measure/cerazette/',
                    '/chemical/0202010D0/',
                    '/bnf/020201/',
                    '/analyse/']:
            url = self.live_server_url + url
            self.browser.get(url)
            self.find_by_xpath(
                '//button[@id="doorbell-button"]')  # Wait for button load
            try:
                el = self.find_visible_by_xpath(
                    '//button[@id="doorbell-button"]')
                el.click()
            except TypeError as e:
                e.args += ("at URL %s" % url,)
                raise

            self.assertTrue(
                self.find_by_xpath('//div[@id="doorbell"]').is_displayed(),
                "get in touch functionality broken at %s" % url
            )

    def test_drug_name_typeahead(self):
        self.browser.get(self.live_server_url + '/analyse/')
        el = self.find_by_xpath(
            '//div[@id="denomIds-wrapper"]'
            '//input[@class="select2-search__field"]')
        el.send_keys("chl")
        # This should succeed; if not, the JSON dropdown-filling has not:
        self.find_by_xpath('//ul[@id="select2-denomIds-results"]//li')

    def test_practice_name_typeahead(self):
        self.browser.get(self.live_server_url + '/analyse/')
        self.find_by_xpath('//span[@id="select2-org-container"]').click()
        self.find_by_xpath(
            '//li[contains(text(), "a practice or practices")]').click()
        el = self.find_by_xpath(
            '//div[@id="orgIds-container"]'
            '//input[@class="select2-search__field"]')
        el.send_keys("ains")
        # This should succeed; if not, the JSON dropdown-filling has not:
        self.find_by_xpath('//ul[@id="select2-orgIds-results"]//li')

    def test_ccg_measures_sorting(self):
        url = self.live_server_url + '/ccg/02Q/measures/'
        self.browser.get(url)
        # The default should be sorting by percentile, then id
        self.assertEqual(self.find_by_xpath(
            "//div[@id='charts']/div[1]").get_attribute("id"),
                         'measure_cerazette')

        # Now click to sort by potential savings
        self.browser.find_element_by_xpath(
            "//button[@data-orderby='savings']").click()

        # hack: not sure of the correct way to await the element
        # being visible.
        import time
        time.sleep(1)
        self.assertEqual(self.find_by_xpath(
            "//div[@id='charts']/div[1]").get_attribute("id"),
                         'measure_keppra')

    def test_ccg_measures_explore_link(self):
        url = self.live_server_url + '/ccg/02Q/'
        self.browser.get(url)
        measure = self.browser.find_element_by_xpath(
            "//div[@id='measure_keppra']")
        self.assertEqual(
            measure.find_element_by_link_text(
                "compare performance with other CCGs").get_attribute('href'),
            '/measure/keppra'
            )
        self.assertEqual(
            measure.find_element_by_link_text(
                "show all practices in this CCG").get_attribute('href'),
            '/ccg/02Q/keppra'
            )


if __name__ == '__main__':
    unittest.main()
