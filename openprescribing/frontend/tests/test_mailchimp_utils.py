from mock import patch, Mock
from unittest import TestCase

from django.http import HttpRequest
from mailchimp3.mailchimpclient import MailChimpError

from frontend.views.mailchimp_utils import mailchimp_subscribe


@patch('frontend.views.mailchimp_utils.MailChimp')
class MailChimpSubscribeTests(TestCase):
    def setUp(self):
        request = HttpRequest()
        request.session = {'newsletter_email': 'alice@example.com'}
        self.args = (
            request,
            'alice@example.com',
            'Alice',
            'Apple',
            'The Orchard',
            'Chief Juicer',
        )

    def test_mailchimp_subscribe_with_existing_subscriber(self, MailChimp):
        self.assertTrue(mailchimp_subscribe(*self.args))

    def test_mailchimp_subscribe_with_new_subscriber(self, MailChimp):
        MailChimp.lists.members.get = Mock(side_effect=MailChimpError())
        self.assertTrue(mailchimp_subscribe(*self.args))

    def test_mailchimp_subscribe_with_blacklisted_subscriber(self, MailChimp):
        MailChimp.return_value.lists.members.get = Mock(side_effect=MailChimpError())
        MailChimp.return_value.lists.members.create = Mock(side_effect=MailChimpError())
        self.assertFalse(mailchimp_subscribe(*self.args))
