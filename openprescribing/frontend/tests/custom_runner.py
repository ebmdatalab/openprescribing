import os
import subprocess

from django.conf import settings
from django.test.runner import DiscoverRunner
from openprescribing.settings import test as test_settings


class AssetBuildingTestRunner(DiscoverRunner):
    # We must run the test server on a port supported by Saucelabs
    os.environ['DJANGO_LIVE_TEST_SERVER_ADDRESS'] = "0.0.0.0:6080"

    def setup_test_environment(self):
        # Use the settings in settings/test.py. Doing it this way
        # means we don't have to remember to specify --settings on the
        # command line when testing.
        for key in dir(test_settings):
            if key.isupper():
                setattr(settings, key, getattr(test_settings, key))

        # Before we load any func tests, ensure we've got assets built
        npm_cmd = "mkdir -p ../../static/js && npm run build"
        subprocess.check_call(
            npm_cmd, shell=True, cwd=settings.SITE_ROOT + '/media/js')

        if not os.environ.get('BROWSER'):
            # Default test environment for Saucelabs
            os.environ['BROWSER'] = 'firefox:47.0:Windows 10'
        super(AssetBuildingTestRunner, self).setup_test_environment()
