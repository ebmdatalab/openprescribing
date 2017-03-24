from django.core.management import call_command
from django.test import TestCase
from frontend.models import Presentation


class CommandsTestCase(TestCase):

    def test_replacements(self):
        Presentation.objects.create(bnf_code='MMMMMMMMMMMMMMM',
                                    name='Drug M')
        Presentation.objects.create(bnf_code='999999999999999',
                                    name='Drug 9')
        Presentation.objects.create(bnf_code='ZZZZZZZZZZZZZZZ',
                                    name='Drug Z')
        fixtures_dir = 'frontend/tests/fixtures/commands/'

        args = [
            fixtures_dir + 'presentation_replacements_2017.txt',
            fixtures_dir + 'presentation_replacements_2016.txt']

        opts = {}
        call_command('generate_presentation_replacements', *args, **opts)

        # Simple replacement
        p = Presentation.objects.get(bnf_code='YYYYYYYYYYYYYYY')
        self.assertEqual(p.replaced_by.bnf_code, 'ZZZZZZZZZZZZZZZ')
        self.assertEqual(p.current_version.bnf_code, 'ZZZZZZZZZZZZZZZ')

        # Double replacement including section change
        p = Presentation.objects.get(bnf_code='777777777777777')
        self.assertEqual(p.current_version.bnf_code, '999999999999999')

        # Deal with loops
        p = Presentation.objects.get(bnf_code='MMMMMMMMMMMMMMM')
        self.assertEqual(p.current_version.bnf_code, 'MMMMMMMMMMMMMMM')
