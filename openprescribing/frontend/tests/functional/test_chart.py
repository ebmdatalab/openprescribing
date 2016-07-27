# -*- coding: utf-8 -*-
import subprocess
import os
import unittest

from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.conf import settings
from django.core import management

from selenium import webdriver

from frontend.tests.test_api_measures import setUpModule as setUpMeasures

# We must run the test server on a port supported by Saucelabs
os.environ['DJANGO_LIVE_TEST_SERVER_ADDRESS'] = "0.0.0.0:6080"


# https://wiki.saucelabs.com/display/DOCS/Platform+Configurator#/
def load_tests(loader, standard_tests, pattern):
    # top level directory cached on loader instance
    if os.environ.get('TEST_SUITE') == 'nonfunctional':
        suite = unittest.TestSuite()
        return suite
    else:
        if not os.environ.get('BROWSER'):
            os.environ['BROWSER'] = 'firefox:47.0:Windows 10'
            # 'safari:9.0:OS X 10.11'
            # 'internet explorer:8.0:Windows 7'
        return standard_tests


def xvfb_exists():
    return subprocess.call(
        "type xvfb-run", shell=True,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE) == 0


class FrontendTest(StaticLiveServerTestCase):

    @classmethod
    def setUpClass(cls):
        # could prob set os.environ['DJANGO_LIVE_TEST_SERVER_ADDRESS']
        super(FrontendTest, cls).setUpClass()
        npm_cmd = "mkdir -p ../../static/js && npm run build"
        cls.use_saucelabs = os.environ.get('TRAVIS') \
            or os.environ.get('USE_SAUCELABS')
        # Should this be run in some environment setup rather than here?
        subprocess.check_call(
            npm_cmd, shell=True, cwd=settings.SITE_ROOT + '/media/js')
        if cls.use_saucelabs:
            browser, version, platform = os.environ['BROWSER'].split(":")
            caps = {'browserName': browser}
            caps['platform'] = platform
            caps['version'] = version
            username = os.environ["SAUCE_USERNAME"]
            access_key = os.environ["SAUCE_ACCESS_KEY"]
            if os.environ.get('TRAVIS'):
                caps["tunnel-identifier"] = os.environ.get(
                    "TRAVIS_JOB_NUMBER", 'n/a')
                caps["build"] = os.environ.get("TRAVIS_BUILD_NUMBER", 'n/a')
                caps["tags"] = ["CI"]
            else:
                caps["tags"] = ["from-dev-sandbox"]
            if os.environ.get('TRAVIS'):
                hub_url = "%s:%s@saucehost:4445" % (username, access_key)
            else:
                hub_url = "%s:%s@localhost:4445" % (username, access_key)
            cls.browser = webdriver.Remote(
                desired_capabilities=caps,
                command_executor="http://%s/wd/hub" % hub_url)
        else:
            if xvfb_exists():
                from pyvirtualdisplay import Display
                cls.display = Display(visible=0, size=(1200, 800))
                cls.display.start()
            cls.browser = webdriver.Firefox()
        cls.browser.maximize_window()
        cls.browser.implicitly_wait(20)

    @classmethod
    def tearDownClass(cls):
        cls.browser.quit()
        if not cls.use_saucelabs and xvfb_exists():
            cls.display.stop()
        super(FrontendTest, cls).tearDownClass()

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
