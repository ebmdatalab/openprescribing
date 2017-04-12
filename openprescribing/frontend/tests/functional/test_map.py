# -*- coding: utf-8 -*-
from selenium_base import SeleniumTestCase


class MapTest(SeleniumTestCase):
    def test_map_slider(self):
        self.browser.get(
            self.live_server_url +
            '/analyse/#org=CCG&numIds=0212000AA&denomIds=2.12&selectedTab=map')

        # Await map
        self.find_by_xpath(
            "//*[@class='leaflet-zoom-animated' and name()='svg']")

        # In the default month (Sept) there is one "maximum" value
        self.assertEqual(
            len(self.browser.find_elements_by_xpath(
                "//*[@fill='#67001f' and name()='path']")),
            1)
        self.assertEqual(
            self.find_by_xpath("//p[@class='chart-sub-title']").text,
            "in Sep '16")

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
        self.assertEqual(
            len(self.browser.find_elements_by_xpath(
                "//*[@fill='#67001f' and name()='path']")),
            2)
        self.assertEqual(
            self.find_by_xpath("//p[@class='chart-sub-title']").text,
            "in Aug '13")
