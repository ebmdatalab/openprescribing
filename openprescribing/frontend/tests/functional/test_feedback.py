# -*- coding: utf-8 -*-
import unittest
import mock

from selenium_base import SeleniumTestCase
from selenium.webdriver.support.ui import WebDriverWait


class FrontendTest(SeleniumTestCase):
    @mock.patch('frontend.views.views.send_mail')
    def test_sending_feedback(self, mock_method):
        self.longMessage = True
        url = self.live_server_url + '/'
        self.browser.get(url)
        jquery = "return $(window).height();"
        window_height = self.browser.execute_script(jquery)
        form = self.find_by_xpath("//div[@id='feedback']")
        self.assertGreater(
            float(form.value_of_css_property('top')[:-2]),
            window_height,
            msg="The feedback form was visible")

        # click "feedback"; the form should appear as a popup
        self.find_by_xpath(
            "//a[contains(@class,'pull_feedback')]").click()
        form = self.find_by_xpath("//div[@id='feedback']")
        WebDriverWait(self.browser, 3).until(
            lambda browser: float(
                form.value_of_css_property('top')[:-2]) < window_height)
        # fill out form
        self.find_by_xpath(
            '//input[@name = "name"]').send_keys("Fred")
        self.find_by_xpath(
            '//input[@name = "email"]').send_keys("fred@fred.com")
        self.find_by_xpath(
            '//textarea[@name = "message"]').send_keys("My message")
        # Send the message
        self.find_by_xpath(
            "//input[@id='send-feedback']").click()
        mock_method.assert_called_with(
            'Feedback',
            'Message posted from http://0.0.0.0:6080/:\n\nMy message',
            '<Fred> fred@fred.com', mock.ANY)
        # Now the popup should disappear again
        WebDriverWait(self.browser, 3).until(
            lambda browser: float(
                form.value_of_css_property('top')[:-2]) >= window_height)

if __name__ == '__main__':
    unittest.main()
