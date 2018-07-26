from django.core.management import call_command
from django.test import TestCase
from frontend.models import PCT


def setUpModule():
    call_command('loaddata', 'frontend/tests/fixtures/ccgs.json',
                 verbosity=0)


def tearDownModule():
    call_command('flush', verbosity=0, interactive=False)


class CommandsTestCase(TestCase):

    def test_import_ccg_boundaries(self):
        args = []
        opts = {
            'filename': ('frontend/tests/fixtures/commands/'
                         'CCG_BSC_Apr2015.TAB')
        }
        call_command('import_ccg_boundaries', *args, **opts)

        pct = PCT.objects.get(code='03Q')
        self.assertAlmostEqual(pct.boundary.centroid.x, -1.0307530606980588)
