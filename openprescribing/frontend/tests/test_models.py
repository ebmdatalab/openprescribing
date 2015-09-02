from django.test import TestCase
from django.core.exceptions import ValidationError
from frontend.models import Chemical, Section, Practice
from frontend.validators import isAlphaNumeric


class ValidationTestCase(TestCase):

    def test_isalphanumeric(self):
        chemical = Chemical(bnf_code='0+9', chem_name='Test')
        with self.assertRaises(ValidationError):
            if chemical.full_clean():
                chemical.save()
        self.assertEqual(Chemical.objects.filter(bnf_code='0+9').count(), 0)

        chemical = Chemical(bnf_code='09', chem_name='Test')
        chemical.full_clean()
        chemical.save()
        self.assertEqual(Chemical.objects.filter(bnf_code='09').count(), 1)


class SectionTestCase(TestCase):

    def setUp(self):
        Section.objects.create(bnf_id='09',
                               name='Nutrition And Blood',
                               bnf_chapter=9)

    def tearDown(self):
        pass

    def test_methods(self):
        section = Section.objects.get(bnf_id='09')

        self.assertEqual(section.get_number_str('12'), '12')
        self.assertEqual(section.get_number_str('2315'), '23.15')
        self.assertEqual(section.get_number_str('1202'), '12.2')
        self.assertEqual(section.get_number_str('090101'), '9.1.1')
        self.assertEqual(section.get_number_str('0901012'), '9.1.1.2')
        self.assertEqual(section.get_number_str('13110112'), '13.11.1.12')

        self.assertEqual(section.strip_zeros(None), None)
        self.assertEqual(section.strip_zeros('0'), None)
        self.assertEqual(section.strip_zeros('00'), None)
        self.assertEqual(section.strip_zeros('01'), 1)
        self.assertEqual(section.strip_zeros('10'), 10)
        self.assertEqual(section.strip_zeros('010'), 10)


class PracticeTestCase(TestCase):

    def setUp(self):
        Practice.objects.create(code='G82650',
                                name='MOCKETTS WOOD SURGERY',
                                address1="THE MOCKETT'S WOOD SURG.",
                                address2='HOPEVILLE AVE ST PETERSY',
                                address3='BROADSTAIRS',
                                address4='KENT',
                                postcode='CT10 2TR')

    def tearDown(self):
        pass

    def test_methods(self):
        practice = Practice.objects.get(code='G82650')

        address = "THE MOCKETT'S WOOD SURG., HOPEVILLE AVE ST PETERSY, "
        address += "BROADSTAIRS, KENT, CT10 2TR"
        self.assertEqual(practice.address_pretty(), address)

        address = "HOPEVILLE AVE ST PETERSY, "
        address += "BROADSTAIRS, KENT, CT10 2TR"
        self.assertEqual(practice.address_pretty_minus_firstline(), address)
