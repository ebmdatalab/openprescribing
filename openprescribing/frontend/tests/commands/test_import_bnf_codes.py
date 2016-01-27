import os
import unittest
from django.core.management import call_command
from django.test import TestCase
from frontend.models import Section, Product, Presentation


class CommandsTestCase(TestCase):

    def test_import_bnf_codes(self):
        args = []
        opts = {
            'filename': 'frontend/tests/fixtures/commands/bnf_codes.csv'
        }
        call_command('import_bnf_codes', *args, **opts)

        r = Product.objects.get(bnf_code='0101010D0AA')
        self.assertEqual(r.name, 'Alum Hydrox + Mag')
        self.assertEqual(r.is_generic, True)
        r = Product.objects.get(bnf_code='0101010C0BB')
        self.assertEqual(r.name, 'Alu-Cap')
        self.assertEqual(r.is_generic, False)
        dummies = Product.objects.filter(name='DUMMY PRODUCT')
        self.assertEqual(dummies.count(), 0)

        r = Presentation.objects.get(bnf_code='0101010D0AAAHAH')
        self.assertEqual(r.name, 'Gppe Susp_Gelusil')
        self.assertEqual(r.is_generic, True)
        r = Presentation.objects.get(bnf_code='0101010C0BDAAAC')
        self.assertEqual(r.name, 'Aludrox_Gel S/F')
        self.assertEqual(r.is_generic, False)

        # Presentations with codes less than 15 chars in length
        # should not be imported.
        r = Presentation.objects.filter(bnf_code='20031000015')
        self.assertEqual(r.count(), 0)

        sections = Section.objects.all()
        self.assertEqual(sections.count(), 6)

        section = Section.objects.get(bnf_id='010101')
        self.assertEqual(section.bnf_chapter, 1)
        self.assertEqual(section.bnf_section, 1)
        self.assertEqual(section.bnf_para, 1)
        self.assertEqual(section.number_str, '1.1.1')

        # Test that trailing zeroes are trimmed
        section = Section.objects.filter(bnf_id='0101010')
        self.assertEqual(section.count(), 0)

        section = Section.objects.get(bnf_id='20')
        self.assertEqual(section.bnf_chapter, 20)
        self.assertEqual(section.bnf_section, None)
        self.assertEqual(section.bnf_para, None)

        # Check that we haven't created dummy entries
        section = Section.objects.filter(bnf_id__startswith='2003')
        self.assertEqual(section.count(), 1)
        section = Section.objects.filter(name__startswith='DUMMY')
        self.assertEqual(section.count(), 0)

        # Test for updated entries
        updated = Presentation.objects.get(bnf_code='0101010A0AAAAAA')
        self.assertEqual(updated.name, 'NEW PRODUCT NAME')
