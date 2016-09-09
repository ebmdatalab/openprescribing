import os
import subprocess

from django.conf import settings
from django.test.runner import DiscoverRunner


class AssetBuildingTestRunner(DiscoverRunner):
    # We must run the test server on a port supported by Saucelabs
    os.environ['DJANGO_LIVE_TEST_SERVER_ADDRESS'] = "0.0.0.0:6080"

    def setup_test_environment(self):
        # Before we load any func tests, ensure we've got assets built
        npm_cmd = "mkdir -p ../../static/js && npm run build"
        subprocess.check_call(
            npm_cmd, shell=True, cwd=settings.SITE_ROOT + '/media/js')

        if not os.environ.get('BROWSER'):
            # Default test environment for Saucelabs
            os.environ['BROWSER'] = 'firefox:47.0:Windows 10'
        super(AssetBuildingTestRunner, self).setup_test_environment()
