import os
import subprocess

from django.conf import settings
from django.test.runner import DiscoverRunner


class AssetBuildingTestRunner(DiscoverRunner):
    """A custom test runner, to support:

      * Building JS and CSS assets when running functional tests
      * Only running functional tests when TEST_SUITE environment says so
      * Custom settings to support running in SauceLabs
    """
    # We must run the test server on a port supported by Saucelabs
    os.environ['DJANGO_LIVE_TEST_SERVER_ADDRESS'] = "0.0.0.0:6080"

    def build_suite(self, test_labels, extra_tests=None, **kwargs):
        if os.environ.get('TEST_SUITE', '') == 'functional' and \
           len(test_labels) == 0:
            test_labels = ['frontend.tests.functional']
        return super(AssetBuildingTestRunner, self).build_suite(
            test_labels, extra_tests, **kwargs)

    def setup_test_environment(self):
        settings.DJANGO_SETTINGS_MODULE = 'frontend.settings.test'
        # Before we load any func tests, ensure we've got assets built
        npm_cmd = "mkdir -p ../../static/js && npm run build"
        if ('SKIP_NPM_BUILD' not in os.environ and
           os.environ.get('TEST_SUITE', '') != 'nonfunctional'):
            subprocess.check_call(
                npm_cmd, shell=True, cwd=settings.SITE_ROOT + '/media/js')
        if not os.environ.get('BROWSER'):
            # Default test environment for Saucelabs
            os.environ['BROWSER'] = 'firefox:latest:Windows 10'
        super(AssetBuildingTestRunner, self).setup_test_environment()
