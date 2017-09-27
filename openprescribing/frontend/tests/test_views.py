import re

from pyquery import PyQuery as pq

from django.conf import settings
from django.core import mail
from django.test import TransactionTestCase

from frontend.models import EmailMessage
from frontend.models import OrgBookmark
from frontend.models import SearchBookmark

from allauth.account.models import EmailAddress


class TestAlertViews(TransactionTestCase):
    fixtures = ['chemicals', 'sections', 'ccgs',
                'practices', 'prescriptions', 'measures']

    def _post_org_signup(self, entity_id, email='foo@baz.com'):
        form_data = {'email': email}
        if len(entity_id) == 3:
            url = "/ccg/%s/" % entity_id
            form_data['pct'] = entity_id
        else:
            url = "/practice/%s/" % entity_id
            form_data['practice'] = entity_id
        return self.client.post(
            url, form_data, follow=True)

    def _post_search_signup(self, url, name, email='foo@baz.com'):
        form_data = {'email': email}
        form_data['url'] = url
        form_data['name'] = name
        return self.client.post(
            '/analyse/', form_data, follow=True)

    def _create_user_and_login(self, email, is_superuser=False):
        from allauth.utils import get_user_model
        user = get_user_model().objects.create(
            username=email, email=email, is_active=True)
        user.set_unusable_password()
        if is_superuser:
            user.is_superuser = True
        user.save()
        EmailAddress.objects.create(user=user,
                                    email=email,
                                    primary=True,
                                    verified=True)
        self.client.force_login(
            user, 'django.contrib.auth.backends.ModelBackend')
        return user

    def test_search_email_invalid(self):
        response = self._post_search_signup('stuff', 'mysearch', email='boo')
        self.assertContains(
            response, "Please enter a valid email address")

    def test_search_email_sent(self):
        response = self._post_search_signup('stuff', 'mysearch')
        self.assertContains(
            response, "Check your email and click the confirmation link")
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("about mysearch", mail.outbox[0].body)

    def test_search_email_copy_kept(self):
        self._post_search_signup('stuff', 'mysearch')
        msg = EmailMessage.objects.first()
        self.assertIn("about mysearch", msg.message.body)
        self.assertIn("foo@baz.com", msg.to)

    def test_search_bookmark_created(self):
        self.assertEqual(SearchBookmark.objects.count(), 0)
        self._post_search_signup('stuff', '%7Emysearch')
        self.assertEqual(SearchBookmark.objects.count(), 1)
        bookmark = SearchBookmark.objects.last()
        self.assertEqual(bookmark.url, 'stuff')
        # Check the name is URL-decoded
        self.assertEqual(bookmark.name, '~mysearch')
        # But it's  not approved (until they log in)
        self.assertFalse(bookmark.approved)

    def test_search_follow_email_link(self):
        self._post_search_signup('stuff', 'mysearch')
        confirm_url = re.match(r".*http://.*(/accounts/confirm-email/.*?)\s",
                               mail.outbox[0].body, re.DOTALL).groups()[0]
        response = self.client.get(confirm_url, follow=True)
        self.assertTemplateUsed(response, 'analyse.html')
        self.assertContains(
            response, "subscribed to monthly alerts about <em>mysearch</em>")
        self.assertTrue(response.context['user'].is_active)
        # The act of logging in approves bookmarks
        bookmark = SearchBookmark.objects.last()
        self.assertTrue(bookmark.approved)

    def test_ccg_email_invalid(self):
        response = self._post_org_signup('03V', email='boo')
        self.assertContains(
            response, "Please enter a valid email address")

    def test_ccg_email_sent(self):
        email = 'a@a.com'
        response = self._post_org_signup('03V', email=email)
        self.assertTrue(response.context['user'].is_anonymous())
        self.assertContains(
            response, "Check your email and click the confirmation link")
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn(email, mail.outbox[0].to)
        self.assertIn("about prescribing in NHS Corby", mail.outbox[0].body)

    def test_ccg_bookmark_added_when_already_logged_in(self):
        email = 'a@a.com'
        self._create_user_and_login(email)
        response = self._post_org_signup('03V', email=email)
        self.assertEqual(response.context['user'].email, email)
        self.assertTemplateUsed(response, 'measures_for_one_ccg.html')
        self.assertContains(response, "Thanks, you're now subscribed")
        self.assertEqual(len(mail.outbox), 0)
        self.assertEqual(OrgBookmark.objects.count(), 1)
        self.assertTrue(OrgBookmark.objects.last().approved)

    def test_bookmark_added_by_other_user_is_unapproved(self):
        # Create user A
        user_a = self._create_user_and_login('a@a.com')
        # Create user B
        self._create_user_and_login('b@b.com')
        # Now user B should not be able to sign up user A to anything
        self._post_org_signup('03V', email='a@a.com')
        created_bookmark = OrgBookmark.objects.last()
        # Note that user A has had a bookmark created (there's nothing
        # to stop anyone signing anyone else up....)
        self.assertTrue(created_bookmark.user.email, 'a@a.com')
        # And they should have an email
        self.assertIn('a@a.com', mail.outbox[0].to)
        # ...but it's an unapproved bookmark...
        self.assertFalse(created_bookmark.approved)
        # ...and user A must reconfirm their identity
        self.assertFalse(user_a.emailaddress_set.first().verified)

    def test_ccg_bookmark_added_for_new_user_when_already_logged_in(self):
        self._create_user_and_login('a@a.com')
        response = self._post_org_signup('03V', email='b@b.com')
        self.assertTrue(response.context['user'].is_anonymous())
        confirm_url = re.match(r".*http://.*(/accounts/confirm-email/.*?)\s",
                               mail.outbox[0].body, re.DOTALL).groups()[0]
        response = self.client.get(confirm_url, follow=True)
        self.assertEqual(response.context['user'].email, 'b@b.com')

    def test_ccg_bookmark_created(self):
        self.assertEqual(OrgBookmark.objects.count(), 0)
        self._post_org_signup('03V')
        self.assertEqual(OrgBookmark.objects.count(), 1)
        bookmark = OrgBookmark.objects.last()
        self.assertEqual(bookmark.pct.code, '03V')

    def test_ccg_follow_email_link(self):
        self._post_org_signup('03V', 'f@frog.com')
        confirm_url = re.match(r".*http://.*(/accounts/confirm-email/.*?)\s",
                               mail.outbox[0].body, re.DOTALL).groups()[0]
        response = self.client.get(confirm_url, follow=True)
        self.assertEqual(response.context['user'].email, 'f@frog.com')
        self.assertContains(
            response, "subscribed to monthly alerts about "
            "<em>prescribing in NHS Corby")
        self.assertTrue(response.context['user'].is_active)

    def test_practice_email_invalid(self):
        response = self._post_org_signup('P87629', email='boo')
        self.assertContains(
            response, "Please enter a valid email address")

    def test_practice_email_sent(self):
        response = self._post_org_signup('P87629')
        self.assertContains(
            response, "Check your email and click the confirmation link")
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("about prescribing in 1/ST Andrews", mail.outbox[0].body)

    def test_practice_bookmark_created(self):
        self.assertEqual(OrgBookmark.objects.count(), 0)
        self._post_org_signup('P87629')
        self.assertEqual(OrgBookmark.objects.count(), 1)
        bookmark = OrgBookmark.objects.last()
        self.assertEqual(bookmark.practice.code, 'P87629')

    def test_practice_follow_email_link(self):
        self._post_org_signup('P87629')
        confirm_url = re.match(r".*http://.*(/accounts/confirm-email/.*?)\s",
                               mail.outbox[0].body, re.DOTALL).groups()[0]
        response = self.client.get(confirm_url, follow=True)
        self.assertContains(
            response, "subscribed to monthly alerts about "
            "<em>prescribing in 1/ST Andrews")
        self.assertTrue(response.context['user'].is_active)


class TestFrontendViews(TransactionTestCase):
    fixtures = ['chemicals', 'sections', 'ccgs',
                'practices', 'prescriptions', 'measures']

    def test_call_view_homepage(self):
        response = self.client.get('')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'index.html')

    def test_javascript_inclusion(self):
        with self.settings(DEBUG=False):
            response = self.client.get('')
            doc = pq(response.content)
            mainjs = doc('script')[-2].attrib['src']
            self.assertIn('openprescribing.min.js', mainjs)
        with self.settings(DEBUG=True, INTERNAL_IPS=('127.0.0.1',)):
            response = self.client.get('')
            doc = pq(response.content)
            mainjs = doc('script')[-2].attrib['src']
            self.assertIn('openprescribing.js', mainjs)

    def test_call_view_analyse(self):
        response = self.client.get('/analyse/')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'analyse.html')
        self.assertNotContains(response, "Preview alert email")

    def test_call_view_bnf_all(self):
        response = self.client.get('/bnf/')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'all_bnf.html')
        self.assertContains(response, '<h1>All BNF sections</h1>')
        doc = pq(response.content)
        sections = doc('#all-results li')
        self.assertEqual(len(sections), 5)
        first_section = doc('#all-results li:first')
        self.assertEqual(first_section.text(), '2: Cardiovascular System')

    def test_call_view_bnf_chapter(self):
        response = self.client.get('/bnf/02/')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'bnf_section.html')
        doc = pq(response.content)
        title = doc('h1')
        self.assertEqual(title.text(), '2: Cardiovascular System')
        subsections = doc('a.subsection')
        self.assertEqual(len(subsections), 2)

    def test_call_view_bnf_section(self):
        response = self.client.get('/bnf/0202/')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'bnf_section.html')
        doc = pq(response.content)
        title = doc('h1')
        self.assertEqual(title.text(), '2.2: Diuretics')
        lead = doc('.lead')
        self.assertEqual(
            lead.text(), 'Part of chapter 2 Cardiovascular System')
        subsections = doc('a.subsection')
        self.assertEqual(len(subsections), 1)

    def test_call_view_bnf_para(self):
        response = self.client.get('/bnf/020201/')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'bnf_section.html')
        doc = pq(response.content)
        title = doc('h1')
        self.assertEqual(
            title.text(), '2.2.1: Thiazides And Related Diuretics')
        lead = doc('.lead')
        self.assertEqual(
            lead.text(),
            'Part of chapter 2 Cardiovascular System , section 2.2 Diuretics')
        subsections = doc('a.subsection')
        self.assertEqual(len(subsections), 0)

    def test_call_view_chemical_all(self):
        response = self.client.get('/chemical/')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'all_chemicals.html')
        self.assertContains(response, '<h1>All chemicals</h1>')
        doc = pq(response.content)
        title = doc('h1')
        self.assertEqual(title.text(), 'All chemicals')
        sections = doc('#all-results li')
        self.assertEqual(len(sections), 4)
        first_section = doc('#all-results li:first')
        self.assertEqual(first_section.text(),
                         'Bendroflumethiazide (0202010B0)')

    def test_call_view_chemical_section(self):
        response = self.client.get('/chemical/0202010D0/')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'chemical.html')
        doc = pq(response.content)
        title = doc('h1')
        self.assertEqual(title.text(), 'Chlorothiazide (0202010D0)')
        lead = doc('.lead')
        self.assertEqual(
            lead.text(),
            ('Part of chapter 2 Cardiovascular System , section 2.2 '
             'Diuretics , paragraph 2.2.1 Thiazides And Related Diuretics')
        )

    def test_call_view_ccg_all(self):
        response = self.client.get('/ccg/')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'all_ccgs.html')
        doc = pq(response.content)
        title = doc('h1')
        self.assertEqual(title.text(), 'All CCGs')
        ccgs = doc('a.ccg')
        self.assertEqual(len(ccgs), 2)

    def test_call_view_ccg_section(self):
        response = self.client.get('/ccg/03V/')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'measures_for_one_ccg.html')
        doc = pq(response.content)
        title = doc('h1')
        self.assertEqual(title.text(), 'CCG: NHS Corby')
        practices = doc('#practices li')
        self.assertEqual(len(practices), 1)

    def test_call_view_practice_all(self):
        response = self.client.get('/practice/')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'all_practices.html')
        doc = pq(response.content)
        title = doc('h1')
        self.assertEqual(title.text(), 'Find a practice')
        practices = doc('#all-results a.practice')
        self.assertEqual(len(practices), 0)

    def test_call_view_practice_section(self):
        response = self.client.get('/practice/P87629/')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'measures_for_one_practice.html')
        doc = pq(response.content)
        title = doc('h1')
        self.assertEqual(title.text(), '1/ST ANDREWS MEDICAL PRACTICE')
        lead = doc('#intro p:first')
        self.assertEqual(
            lead.text(),
            ('Address: ST.ANDREWS MEDICAL CENTRE, 30 RUSSELL STREET '
             'ECCLES, MANCHESTER, M30 0NU'))
        lead = doc('.lead:last')

    def test_call_view_measure_ccg(self):
        response = self.client.get('/ccg/03V/')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'measures_for_one_ccg.html')
        doc = pq(response.content)
        title = doc('h1')
        self.assertEqual(title.text(), 'CCG: NHS Corby')
        practices = doc('#practices li')
        self.assertEqual(len(practices), 1)

    def test_call_view_measure_practice(self):
        response = self.client.get('/practice/P87629/')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'measures_for_one_practice.html')
        doc = pq(response.content)
        title = doc('h1')
        self.assertEqual(title.text(), '1/ST ANDREWS MEDICAL PRACTICE')

    def test_call_view_measure_practices_in_ccg(self):
        response = self.client.get('/ccg/03V/cerazette/')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'measure_for_practices_in_ccg.html')
        doc = pq(response.content)
        title = doc('h1')
        t = ('Cerazette vs. Desogestrel by GP practices '
             'in NHS Corby')
        self.assertEqual(title.text(), t)

    def test_call_view_practice_redirect(self):
        response = self.client.get('/practice/P87629/measures/')
        self.assertEqual(response.status_code, 301)

    def test_call_view_ccg_redirect(self):
        response = self.client.get('/ccg/03V/measures/')
        self.assertEqual(response.status_code, 301)

    def test_gdoc_inclusion(self):
        for doc_id in settings.GDOC_DOCS.keys():
            response = self.client.get("/docs/%s/" % doc_id)
            self.assertEqual(response.status_code, 200)


class TestPPUViews(TransactionTestCase):
    fixtures = ['ccgs', 'importlog', 'dmdproducts',
                'practices', 'prescriptions', 'presentations']

    def test_practice_price_per_unit(self):
        response = self.client.get('/practice/P87629/price_per_unit/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['entity'].code, 'P87629')

    def test_ccg_price_per_unit(self):
        response = self.client.get('/ccg/03V/price_per_unit/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['entity'].code, '03V')
        self.assertEqual(response.context['date'].strftime('%Y-%m-%d'),
                         '2014-11-01')

    def test_price_per_unit_histogram_with_ccg(self):
        response = self.client.get('/ccg/03V/0202010F0AAAAAA/price_per_unit/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['highlight_name'], 'NHS Corby')
        self.assertEqual(response.context['date'].strftime('%Y-%m-%d'),
                         '2014-11-01')

    def test_price_per_unit_histogram_with_practice(self):
        response = self.client.get(
            '/practice/P87629/0202010F0AAAAAA/price_per_unit/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['highlight_name'],
                         '1/ST Andrews Medical Practice')
        self.assertEqual(response.context['date'].strftime('%Y-%m-%d'),
                         '2014-11-01')
