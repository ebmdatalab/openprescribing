# -*- coding: utf-8 -*-
# All the tests in this file fail in CI (BrowserStack running in Github
# Actions) but pass locally (though a different set of tests fail locally and
# pass in CI). Given that we were previously ignoring the functional test suite
# altogether when running under Travis/Saucelabs and that we have no time or
# funding to work on this, we've decided the least bad option is to mark these
# tests as expected failures for now.
#
# I've re-run the tests several times and they appear to at least be consistent
# failures, unlike the intermittent ones we had with Travis/Saucelabs.
import unittest

from selenium.webdriver.common.by import By

from .selenium_base import SeleniumTestCase


class MapTest(SeleniumTestCase):
    # These tests run against a MockAPIServer started by the
    # custom_runner
    def test_map_slider(self):
        self.browser.get(
            self.live_server_url
            + "/analyse/#org=CCG&numIds=0212000AA&denomIds=2.12&selectedTab=map"
        )

        # Await map
        self.find_by_xpath("//*[@class='leaflet-zoom-animated' and name()='svg']")

        # In the default month (Sept) there is one "maximum" value
        self.assertEqual(
            len(
                self.browser.find_elements(
                    By.XPATH, "//*[@fill='#67001f' and name()='path']"
                )
            ),
            1,
        )
        self.assertEqual(
            self.find_by_xpath("//p[@class='chart-sub-title']").text, "in Sep '16"
        )

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
            len(
                self.browser.find_elements(
                    By.XPATH, "//*[@fill='#67001f' and name()='path']"
                )
            ),
            2,
        )
        self.assertEqual(
            self.find_by_xpath("//p[@class='chart-sub-title']").text, "in Apr '13"
        )


class SmallListTest(SeleniumTestCase):
    # These tests run against a MockAPIServer started by the
    # custom_runner
    def test_nothing_hidden_by_default(self):
        self.browser.get(
            self.live_server_url
            + (
                "/analyse/#org=practice&orgIds=X&numIds=0212000AA"
                "&denom=total_list_size&selectedTab=summary"
            )
        )
        warning = self.find_visible_by_xpath("//div[contains(@class, 'toggle')]/a")
        self.assertIn("Remove", warning.text)
        xlabels = self.find_by_xpath("//*[contains(@class, 'highcharts-xaxis-labels')]")
        self.assertIn("GREEN", xlabels.text)
        warning.click()
        warning = self.find_by_xpath("//div[contains(@class, 'toggle')]/a")
        self.assertIn("Show", warning.text)
        xlabels = self.find_by_xpath("//*[contains(@class, 'highcharts-xaxis-labels')]")
        self.assertNotIn("GREEN", xlabels.text)


class AnalyseSummaryTotalsTest(SeleniumTestCase):
    @unittest.expectedFailure
    def test_summary_totals_on_analyse_page(self):
        self.browser.get(self.live_server_url + "/analyse/#org=CCG&numIds=0212000AA")
        expected = {
            "panel-heading": (
                "Total prescribing for Rosuvastatin Calcium across all "
                "Sub-ICB Locations in NHS England"
            ),
            "js-selected-month": "Sep '16",
            "js-financial-year-range": "Apr—Sep '16",
            "js-year-range": "Oct '15—Sep '16",
            "js-cost-month-total": "29,720",
            "js-cost-financial-year-total": "178,726",
            "js-cost-year-total": "379,182",
            "js-items-month-total": "1,669",
            "js-items-financial-year-total": "9,836",
            "js-items-year-total": "20,622",
        }
        for classname, value in expected.items():
            selector = (
                '//*[@id="{id}"]'
                '//*[contains(concat(" ", @class, " "), " {classname} ")]'.format(
                    id="js-summary-totals", classname=classname
                )
            )
            element = self.find_visible_by_xpath(selector)
            self.assertTrue(
                element.is_displayed(), ".{} is not visible".format(classname)
            )
            self.assertEqual(element.text.strip(), value)
