from django.test import TestCase
from django.core.exceptions import ValidationError

from frontend.models import Chemical
from frontend.models import EmailMessage
from frontend.models import MailLog
from frontend.models import PCT
from frontend.models import Practice
from frontend.models import Presentation
from frontend.models import SearchBookmark
from frontend.models import Section
from frontend.models import User


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

    def test_name_titlecase(self):
        practice = Practice.objects.get(code='G82650')
        self.assertEqual(practice.cased_name, 'Mocketts Wood Surgery')

    def test_inactive_status_suffix(self):
        practice = Practice.objects.get(code='G82650')
        self.assertEqual(practice.inactive_status_suffix(), '')
        practice.status_code = 'D'
        self.assertEqual(practice.inactive_status_suffix(), ' - Dormant')


class TestMessage(object):
    to = ['foo']
    subject = 'subject'
    tags = []
    extra_headers = {'message-id': '123'}

    def __eq__(self, other):
        match = True
        for attr in dir(self):
            if not attr.startswith('_'):
                match = getattr(self, attr) == getattr(other, attr)
                if not match:
                    return False
        return match


class EmailMessageTestCase(TestCase):
    def test_message_pickled(self):
        msg = TestMessage()
        m = EmailMessage.objects.create_from_message(msg)
        self.assertEqual(msg, m.message)

    def test_message_id_assertion(self):
        msg = TestMessage()
        msg.extra_headers = {}
        with self.assertRaises(StandardError):
            EmailMessage.objects.create_from_message(msg)


class SearchBookmarkTestCase(TestCase):
    fixtures = ['users']

    def test_name_is_truncated(self):
        very_long_name = 'l' * 2000
        SearchBookmark.objects.create(
            name=very_long_name,
            user=User.objects.first(),
            url='foo'
        )
        self.assertEqual(len(SearchBookmark.objects.first().name), 200)


class MailLogTestCase(TestCase):
    def test_metadata_nests_correctly(self):
        MailLog.objects.create(
            recipient='me',
            event_type='accepted',
            metadata={'thing': ['foo']}
        )
        self.assertEqual(MailLog.objects.first().metadata['thing'][0], 'foo')

    def test_no_constraint_on_message_id(self):
        MailLog.objects.create(
            recipient='me',
            event_type='accepted',
            metadata={'thing': ['foo']},
            message_id='123'
        )
        self.assertEqual(MailLog.objects.first().message_id, '123')

    def test_bounced_subject_no_stored_email(self):
        MailLog.objects.create(
            recipient='me',
            event_type='bounced',
            metadata={},
            message_id='123'
        )
        self.assertEqual(
            MailLog.objects.first().subject_from_metadata(), 'n/a')

    def test_bounced_subject_no_message_id(self):
        MailLog.objects.create(
            recipient='me',
            event_type='bounced',
            metadata={}
        )
        self.assertEqual(
            MailLog.objects.first().subject_from_metadata(), 'n/a')


class PCTTestCase(TestCase):
    def test_name_titlecase(self):
        PCT.objects.create(
            code='asd',
            org_type='CCG',
            name='NHS BACON CCG'
        )
        self.assertEqual(PCT.objects.first().cased_name, 'NHS Bacon CCG')


class PresentationTestCase(TestCase):
    fixtures = ['presentations', 'dmdproducts']

    def test_manager(self):
        current = Presentation.objects.current()
        old_count = len(current)
        to_make_not_current = current[0]
        to_make_not_current.replaced_by = current[1]
        to_make_not_current.save()
        self.assertEqual(len(Presentation.objects.current()), old_count - 1)

    def test_dmd_product_which_exists(self):
        p = Presentation.objects.get(pk='0202010F0AAAAAA')
        self.assertEqual(p.dmd_product.vpid, 318248001)

    def test_dmd_product_which_does_not_exist(self):
        p = Presentation.objects.get(pk='0202010B0AAACAC')
        self.assertEqual(p.dmd_product, None)

    def test_product_name_with_dmd_product(self):
        p = Presentation.objects.get(pk='0202010F0AAAAAA')
        self.assertEqual(p.product_name, 'Verapamil 160mg tablets')

    def test_product_name_without_dmd_product(self):
        p = Presentation.objects.get(pk='0202010B0AAACAC')
        self.assertEqual(p.product_name, 'Bendroflumethiazide_Tab 5mg')


class TestPresentationDMDLinks(TestCase):
    fixtures = ['presentations_and_dmd_objs']

    def test_dmd_info(self):
        # Testing dmd_info() thoroughly would require setting up a large amount
        # of test data.  Constructing this manually is a lot of work.  Instead,
        # I have generated fixtures from the test data in dmd2, which covers a
        # range of the kinds of relationships between presentations and dm+d
        # objects.

        # We check that dmd_info() returns something sensible for each key for
        # two presentations.

        # Diclofenac Sod_Gel 2.32%
        p = Presentation.objects.get(bnf_code='1003020U0AAAIAI')
        info = p.dmd_info()
        self.assertEqual(
            info['prescribability_statuses'],
            'Valid as a prescribable product'
        )
        self.assertEqual(info['tariff_categories'], 'Part VIIIA Category C')

        # Voltarol 12 Hour Emulgel P_Gel 2.32%
        p = Presentation.objects.get(bnf_code='1003020U0BBADAI')
        info = p.dmd_info()
        self.assertEqual(info['availability_restrictions'], 'None')

        # We check that most of the code paths for producing dmd_info() are
        # exercised.
        for p in Presentation.objects.all():
            p.dmd_info()
