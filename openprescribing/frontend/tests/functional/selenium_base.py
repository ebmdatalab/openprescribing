import os
import subprocess
import unittest

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities

from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.conf import settings


# Django 1.11 removes the ability to supply a port range for liveserver tests, so we replicate that here.
# See: https://code.djangoproject.com/ticket/28212 and https://code.djangoproject.com/ticket/26011
available_test_ports = iter(range(6080, 6580))


def use_saucelabs():
    return os.environ.get('TRAVIS') or os.environ.get('USE_SAUCELABS')


@unittest.skipIf(
    os.environ.get('TEST_SUITE') == 'nonfunctional',
    "nonfunctional tests specified in TEST_SUITE environment variable")
class SeleniumTestCase(StaticLiveServerTestCase):

    host = '0.0.0.0'

    @classmethod
    def use_xvfb(cls):
        if not os.environ.get('SHOW_BROWSER', False):
            return subprocess.call(
                "type xvfb-run", shell=True,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE) == 0
        else:
            return False

    @classmethod
    def get_firefox_driver(cls):
        caps = DesiredCapabilities.FIREFOX
        fp = webdriver.FirefoxProfile()
        # https://github.com/SeleniumHQ/selenium/issues/2701#issuecomment-275895137
        fp.set_preference('browser.tabs.remote.autostart.2', False)
        caps["marionette"] = True
        return webdriver.Firefox(
            capabilities=caps,
            firefox_profile=fp,
            log_path="%s/logs/webdriver.log" % settings.INSTALL_ROOT)

    @classmethod
    def setUpClass(cls):
        cls.port = next(available_test_ports)
        if use_saucelabs():
            browser, version, platform = os.environ['BROWSER'].split(":")
            caps = {'browserName': browser}
            caps['platform'] = platform
            caps['version'] = version
            caps['screenResolution'] = '1600x1200'
            # Disable slow script warning in IE
            caps['prerun'] = {
                'executable': ('https://raw.githubusercontent.com/'
                               'ebmdatalab/openprescribing/'
                               'master/scripts/setup_ie_8.bat'),
                'background': 'false'
            }
            username = os.environ["SAUCE_USERNAME"]
            access_key = os.environ["SAUCE_ACCESS_KEY"]
            if os.environ.get('TRAVIS'):
                caps["tunnel-identifier"] = os.environ.get(
                    "TRAVIS_JOB_NUMBER", 'n/a')
                caps["build"] = os.environ.get("TRAVIS_BUILD_NUMBER", 'n/a')
                caps["tags"] = ["CI"]
            else:
                caps["tags"] = ["from-dev-sandbox"]
            if os.environ.get('TRAVIS') or os.path.exists('/.dockerenv'):
                hub_url = "%s:%s@saucehost:4445" % (username, access_key)
            else:
                hub_url = "%s:%s@localhost:4445" % (username, access_key)
            cls.browser = webdriver.Remote(
                desired_capabilities=caps,
                command_executor="http://%s/wd/hub" % hub_url)
        else:
            if cls.use_xvfb():
                from pyvirtualdisplay import Display
                cls.display = Display(visible=0, size=(1200, 800))
                cls.display.start()
            try:
                cls.browser = cls.get_firefox_driver()
            except Exception:
                if not use_saucelabs() and cls.use_xvfb():
                    cls.display.stop()
                    raise
        cls.browser.maximize_window()
        cls.browser.implicitly_wait(1)
        super(SeleniumTestCase, cls).setUpClass()

    @classmethod
    def tearDownClass(cls):
        cls.browser.quit()
        if not use_saucelabs() and cls.use_xvfb():
            cls.display.stop()
        super(SeleniumTestCase, cls).tearDownClass()

    def _find_and_wait(self, locator, waiter):
        if use_saucelabs():
            wait = 60
        else:
            wait = 5
        try:
            element = WebDriverWait(self.browser, wait).until(
                waiter((By.XPATH, locator))
            )
            return element
        except TimeoutException:
            raise AssertionError("Expected to find element %s" % locator)

    def find_by_xpath(self, locator):
        return self._find_and_wait(locator, EC.presence_of_element_located)

    def find_visible_by_xpath(self, locator):
        return self._find_and_wait(locator, EC.visibility_of_element_located)
