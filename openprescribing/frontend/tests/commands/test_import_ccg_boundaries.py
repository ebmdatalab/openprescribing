from django.core.management import call_command
from django.test import TestCase
from frontend.models import PCT


class CommandsTestCase(TestCase):

    fixtures = ['ccgs']

    def test_import_ccg_boundaries(self):
        args = []
        opts = {
            'filename': ('frontend/tests/fixtures/commands/'
                         'CCG_BSC_Apr2015.TAB')
        }
        call_command('import_ccg_boundaries', *args, **opts)

        pct = PCT.objects.get(code='03Q')
        self.assertAlmostEqual(pct.boundary.centroid.x, -1.0307530606980588)
