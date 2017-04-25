from django.core.management import call_command
from django.test import TestCase
from frontend.models import Chemical
from frontend.models import Presentation
from frontend.models import Product
from frontend.models import Section

from mock import patch
from mock import MagicMock


@patch('frontend.management.commands.generate_presentation_replacements'
       '.cleanup_empty_classes')
@patch('frontend.management.commands.generate_presentation_replacements'
       '.load_data_from_file')
@patch('frontend.management.commands.generate_presentation_replacements'
       '.create_bigquery_views')
class CommandsTestCase(TestCase):
    def setUp(self):
        Section.objects.create(bnf_id='0000',
                               name='Subsection 0.0',
                               bnf_chapter=0,
                               bnf_section=0,
                               bnf_para=0)
        Section.objects.create(bnf_id='9999',
                               name='Subsection 9.9',
                               bnf_chapter=0,
                               bnf_section=0,
                               bnf_para=0)
        Section.objects.create(bnf_id='777777',
                               name='Para 7.7.7',
                               bnf_chapter=0,
                               bnf_section=0,
                               bnf_para=0)
        Section.objects.create(bnf_id='222222',
                               name='Para 2.2.2',
                               bnf_chapter=0,
                               bnf_section=0,
                               bnf_para=0)
        Chemical.objects.create(bnf_code='ZZZZZZZZZ',
                                chem_name='Chemical Z')
        Chemical.objects.create(bnf_code='YYYYYYYYY',
                                chem_name='Chemical Y')
        Chemical.objects.create(bnf_code='111111111',
                                chem_name='Chemical 1')
        Product.objects.create(bnf_code='33333333333',
                               name='Product 3')
        Product.objects.create(bnf_code='44444444444',
                               name='Product 4')
        Presentation.objects.create(bnf_code='MMMMMMMMMMMMMMM',
                                    name='Drug M')
        Presentation.objects.create(bnf_code='999999999999999',
                                    name='Drug 9')
        Presentation.objects.create(bnf_code='ZZZZZZZZZZZZZZZ',
                                    name='Drug Z')
        fixtures_dir = 'frontend/tests/fixtures/commands/'

        self.args = [
            fixtures_dir + 'presentation_replacements_2017.txt',
            fixtures_dir + 'presentation_replacements_2016.txt']
        self.opts = {}

    def test_replacements(
            self,
            mock_create_view,
            mock_loader,
            mock_empty_class_csv_getter):
        # Simple replacement
        call_command(
            'generate_presentation_replacements', *self.args, **self.opts)
        p = Presentation.objects.get(bnf_code='YYYYYYYYYYYYYYY')
        self.assertEqual(p.replaced_by.bnf_code, 'ZZZZZZZZZZZZZZZ')
        self.assertEqual(p.current_version.bnf_code, 'ZZZZZZZZZZZZZZZ')

        # Double replacement including section change
        p = Presentation.objects.get(bnf_code='777777777777777')
        self.assertEqual(p.current_version.bnf_code, '999999999999999')

        # Deal with loops
        p = Presentation.objects.get(bnf_code='MMMMMMMMMMMMMMM')
        self.assertEqual(p.current_version.bnf_code, 'MMMMMMMMMMMMMMM')

    def test_chemical_currency(
            self,
            mock_create_view,
            mock_loader,
            mock_empty_class_csv_getter):
        call_command(
            'generate_presentation_replacements', *self.args, **self.opts)
        self.assertEqual(
            Chemical.objects.get(pk='YYYYYYYYY').is_current, False)
        self.assertEqual(
            Chemical.objects.get(pk='ZZZZZZZZZ').is_current, True)
        self.assertEqual(
            Chemical.objects.get(pk='111111111').is_current, True)
        # Subsection
        self.assertEqual(
            Section.objects.get(pk='0000').is_current, False)
        self.assertEqual(
            Section.objects.get(pk='9999').is_current, True)
        # Paragraph
        self.assertEqual(
            Section.objects.get(pk='777777').is_current, False)
        self.assertEqual(
            Section.objects.get(pk='222222').is_current, True)
        # Products
        self.assertEqual(
            Product.objects.get(pk='44444444444').is_current, False)
        self.assertEqual(
            Product.objects.get(pk='33333333333').is_current, True)

    @patch('frontend.management.commands.generate_presentation_replacements'
           '.csv')
    def test_bigquery_csv(
            self,
            mock_csv,
            mock_create_view,
            mock_loader,
            mock_empty_class_csv_getter):
        call_command(
            'generate_presentation_replacements', *self.args, **self.opts)
        mock_loader.assert_called()
        writerow = mock_csv.writer.return_value.writerow
        writerow.assert_any_call(['LLLLLLLLLLLLLLL', 'LLLLLLLLLLLLLLL'])
        writerow.assert_any_call(['000999999999999', '999999999999999'])
        writerow.assert_any_call(['MMMMMMMMMMMMMMM', 'MMMMMMMMMMMMMMM'])
        writerow.assert_any_call(['YYYYYYYYYYYYYYY', 'ZZZZZZZZZZZZZZZ'])
        writerow.assert_any_call(['777777777777777', '999999999999999'])
