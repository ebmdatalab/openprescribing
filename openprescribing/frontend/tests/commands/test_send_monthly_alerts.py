# -*- coding: utf-8 -*-
import re
import unittest

from mock import patch
from mock import ANY

from django.conf import settings
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase
from frontend.models import Measure
from frontend.management.commands.send_monthly_alerts import Command

CMD_NAME = 'send_monthly_alerts'


class AnyStringWith(str):
    def __eq__(self, other):
        return self in other


class ValidateOptionsTestCase(unittest.TestCase):
    def _defaultOpts(self, **extra):
        default = {
            'url': None,
            'ccg': None,
            'practice': None,
            'recipient_email': None,
            'url': None
        }
        for k, v in extra.items():
            default[k] = v
        return default

    def test_options_depended_on_by_recipient_email(self):
        opts = self._defaultOpts(url='thing')
        with self.assertRaises(CommandError):
            Command().validate_options(**opts)
        opts = self._defaultOpts(ccg='thing')
        with self.assertRaises(CommandError):
            Command().validate_options(**opts)
        opts = self._defaultOpts(practice='thing')
        with self.assertRaises(CommandError):
            Command().validate_options(**opts)

        opts = self._defaultOpts(practice='thing', recipient_email='thing')
        Command().validate_options(**opts)

    def test_incompatibile_options(self):
        opts = self._defaultOpts(url='thing', ccg='thing')
        with self.assertRaises(CommandError):
            Command().validate_options(**opts)
        opts = self._defaultOpts(url='thing', practice='thing')
        with self.assertRaises(CommandError):
            Command().validate_options(**opts)


class GetBookmarksTestCase(TestCase):
    fixtures = ['bookmark_alerts']

    def test_get_org_bookmarks_without_options(self):
        bookmarks = Command().get_org_bookmarks(recipient_email=None)
        active = all([x.user.is_active for x in bookmarks])
        self.assertEqual(len(bookmarks), 2)
        self.assertTrue(active)

    def test_get_org_bookmarks_with_options(self):
        bookmarks = Command().get_org_bookmarks(
            recipient_email='s@s.com',
            ccg='03V',
            practice='P87629'
        )
        self.assertEqual(len(bookmarks), 1)
        self.assertEqual(bookmarks[0].user.email, 's@s.com')
        self.assertTrue(bookmarks[0].user.profile.key)
        self.assertTrue(bookmarks[0].user.id)
        self.assertEqual(bookmarks[0].pct.code, '03V')
        self.assertEqual(bookmarks[0].practice.code, 'P87629')

    def test_get_search_bookmarks_without_options(self):
        bookmarks = Command().get_search_bookmarks(recipient_email=None)
        active = all([x.user.is_active for x in bookmarks])
        self.assertEqual(len(bookmarks), 1)
        self.assertEqual(bookmarks[0].url, 'foo')
        self.assertTrue(active)

    def test_get_search_bookmarks_with_options(self):
        bookmarks = Command().get_search_bookmarks(
            recipient_email='s@s.com',
            url='frob', search_name='baz')
        self.assertEqual(len(bookmarks), 1)
        self.assertEqual(bookmarks[0].user.email, 's@s.com')
        self.assertTrue(bookmarks[0].user.profile.key)
        self.assertTrue(bookmarks[0].user.id)
        self.assertEqual(bookmarks[0].url, 'frob')


@patch('frontend.views.bookmark_utils.InterestingMeasureFinder')
@patch('frontend.views.bookmark_utils.EmailMultiAlternatives')
@patch('frontend.views.bookmark_utils.attach_image')
class OrgEmailTestCase(TestCase):
    fixtures = ['bookmark_alerts', 'measures']

    def test_email_recipient(self, attach_image, email, finder):
        test_context = _makeContext()
        call_mocked_command(test_context, finder)
        email.assert_any_call(
            ANY,  # subject
            ANY,  # body
            settings.SUPPORT_EMAIL,
            ['s@s.com']
        )
        email.return_value.send.assert_any_call()

    def test_email_body_no_data(self, attach_image, email, finder):
        test_context = _makeContext()
        call_mocked_command(test_context, finder)
        attachment = email.return_value.attach_alternative
        # Name of the practice
        attachment.assert_called_once_with(
            AnyStringWith('1/ST ANDREWS MEDICAL PRACTICE'), 'text/html')
        # Unsubscribe link
        attachment.assert_called_once_with(
            AnyStringWith('/bookmarks/dummykey'), 'text/html')

        attachment.assert_called_once_with(
            AnyStringWith("We've no new information"), 'text/html')

    def test_email_body_has_ga_tracking(self, attach_image, email, finder):
        measure = Measure.objects.get(pk='cerazette')
        call_mocked_command(
            _makeContext(declines=[(measure, 99.92, 0.12, 10.002)]),
            finder)
        attachment = email.return_value.attach_alternative
        body = attachment.call_args[0][0]
        self.assertRegexpMatches(
            body, '<a href=".*&utm_content=.*#cerazette".*>')

    def test_email_body_declines(self, attach_image, email, finder):
        attach_image.return_value = 'unique-image-id'
        measure = Measure.objects.get(pk='cerazette')
        call_mocked_command(
            _makeContext(declines=[(measure, 99.92, 0.12, 10.002)]),
            finder)
        attachment = email.return_value.attach_alternative
        attachment.assert_called_once_with(
            AnyStringWith("this practice slipped"), 'text/html')

        body = attachment.call_args[0][0]
        self.assertRegexpMatches(
            body, 'slipped massively .* on '
            '<a href=".*/practice/P87629/.*#cerazette".*>'
            'Cerazette vs. Desogestrel</a>')
        self.assertIn('<span class="worse"', body)
        self.assertIn('<img src="cid:unique-image-id', body)
        self.assertNotIn("Your best prescribing areas", body)
        self.assertNotIn("Cost savings", body)

    def test_email_body_two_declines(self, attach_image, email, finder):
        measure = Measure.objects.get(pk='cerazette')
        call_mocked_command(
            _makeContext(declines=[
                (measure, 99.92, 0.12, 10.002),
                (measure, 30, 10, 0),
            ]),
            finder)
        attachment = email.return_value.attach_alternative
        body = attachment.call_args[0][0]
        self.assertRegexpMatches(
            body, 'It also slipped considerably')

    def test_email_body_three_declines(self, attach_image, email, finder):
        measure = Measure.objects.get(pk='cerazette')
        call_mocked_command(
            _makeContext(declines=[
                (measure, 99.92, 0.12, 10.002),
                (measure, 30, 10, 0),
                (measure, 20, 10, 0)
            ]),
            finder)
        attachment = email.return_value.attach_alternative
        body = attachment.call_args[0][0]
        self.assertRegexpMatches(
            body, 'It also slipped:')
        self.assertRegexpMatches(
            body, re.compile('<ul.*<li>considerably on.*'
                             '<li>moderately on.*</ul>', re.DOTALL))

    def test_email_body_worst(self, attach_image, email, finder):
        measure = Measure.objects.get(pk='cerazette')
        attach_image.return_value = 'unique-image-id'
        call_mocked_command(_makeContext(worst=[measure]), finder)
        attachment = email.return_value.attach_alternative
        attachment.assert_called_once_with(
            AnyStringWith("We've found"), 'text/html')

        body = attachment.call_args[0][0]
        self.assertRegexpMatches(
            body, re.compile(
                'the worst 10% on.*<a href=".*/practice/P87629'
                '/.*#cerazette".*>'
                "Cerazette vs. Desogestrel</a>", re.DOTALL))
        self.assertIn('<img src="cid:unique-image-id', body)

    def test_email_body_three_worst(self, attach_image, email, finder):
        measure = Measure.objects.get(pk='cerazette')
        call_mocked_command(
            _makeContext(worst=[measure, measure, measure]), finder)
        attachment = email.return_value.attach_alternative
        body = attachment.call_args[0][0]
        self.assertRegexpMatches(
            body, 'It was also in the worst 10% on:')
        self.assertRegexpMatches(
            body, re.compile('<ul.*<li>.*Desogestrel.*'
                             '<li>.*Desogestrel.*</ul>', re.DOTALL))

    def test_email_body_two_savings(self, attach_image, email, finder):
        measure = Measure.objects.get(pk='cerazette')
        call_mocked_command(
            _makeContext(possible_savings=[
                (measure, 9.9), (measure, 1.12)]),
            finder)
        attachment = email.return_value.attach_alternative
        body = attachment.call_args[0][0]
        self.assertIn(
            "These add up to around <b>£10</b> of "
            "potential savings".decode('utf-8'),
            body)
        self.assertRegexpMatches(
            body, '<li.*>\n<b>£10</b> on <a href=".*/practice/P87629'
            '/.*#cerazette".*>'
            "Cerazette vs. Desogestrel</a>".decode('utf-8'))

    def test_email_body_one_saving(self, attach_image, email, finder):
        measure = Measure.objects.get(pk='cerazette')
        call_mocked_command(
            _makeContext(possible_savings=[(measure, 9.9)]), finder)
        attachment = email.return_value.attach_alternative
        body = attachment.call_args[0][0]
        self.assertIn(
            "if it had prescribed in line with the average practice",
            body)
        self.assertRegexpMatches(
            body, 'it could have saved about <b>£10</b> on '
            '<a href=".*/practice/P87629/.*#cerazette".*>'
            "Cerazette vs. Desogestrel</a>".decode('utf-8'))

    def test_email_body_achieved_saving(self, attach_image, email, finder):
        measure = Measure.objects.get(pk='cerazette')
        call_mocked_command(
            _makeContext(achieved_savings=[(measure, 9.9)]), finder)
        attachment = email.return_value.attach_alternative
        body = attachment.call_args[0][0]
        self.assertIn(
            "this practice saved around <b>£10".decode('utf-8'),
            body)

    def test_email_body_two_achieved_savings(
            self, attach_image, email, finder):
        measure = Measure.objects.get(pk='cerazette')
        call_mocked_command(
            _makeContext(
                achieved_savings=[(measure, 9.9), (measure, 12.0)]),
            finder)
        attachment = email.return_value.attach_alternative
        body = attachment.call_args[0][0]
        self.assertIn(
            "<li>\n<b>£10</b> on".decode('utf-8'),
            body)
        self.assertIn(
            "<li>\n<b>£10</b> on".decode('utf-8'),
            body)

    def test_email_body_total_savings(self, attach_image, email, finder):
        call_mocked_command(
            _makeContext(possible_top_savings_total=9000.1), finder)
        attachment = email.return_value.attach_alternative
        body = attachment.call_args[0][0]
        self.assertIn(
            "it could save around <b>£9,000</b>".decode('utf-8'),
            body)


@patch('frontend.views.bookmark_utils.EmailMultiAlternatives')
@patch('frontend.views.bookmark_utils.attach_image')
class SearchEmailTestCase(TestCase):
    fixtures = ['bookmark_alerts']

    def test_all_recipients(self, attach_image, email):
        call_command(CMD_NAME)
        email.assert_any_call(
            ANY,  # subject
            ANY,  # body
            settings.SUPPORT_EMAIL,
            ['foo@baz.com']
        )
        self.assertEqual(email.call_count, 3)
        email.return_value.send.assert_any_call()

    def test_email_recipient(self, attach_image, email):
        opts = {'recipient_email': 's@s.com',
                'url': 'something'}
        call_command(CMD_NAME, **opts)
        email.assert_any_call(
            ANY,  # subject
            ANY,  # body
            settings.SUPPORT_EMAIL,
            ['s@s.com']
        )
        self.assertEqual(email.call_count, 1)
        email.return_value.send.assert_any_call()

    def test_email_body(self, attach_image, email):
        opts = {'recipient_email': 's@s.com',
                'url': 'something',
                'search_name': 'some name'}
        call_command(CMD_NAME, **opts)
        attachment = email.return_value.attach_alternative
        attachment.assert_called_once_with(
            AnyStringWith('some name'), 'text/html')

        # Unsubscribe link
        attachment.assert_called_once_with(
            AnyStringWith('/bookmarks/dummykey'), 'text/html')
        body = attachment.call_args[0][0]
        self.assertRegexpMatches(
            body, '<a href="http://localhost/analyse/.*#%s' % 'something')


def call_mocked_command(context, mock_finder, **opts):
    mock_finder.return_value.context_for_org_email.return_value = context
    default_opts = {'recipient_email': 's@s.com',
                    'ccg': '03V',
                    'practice': 'P87629'}
    for k, v in opts.items():
        default_opts[k] = v
    call_command(CMD_NAME, **default_opts)


def _makeContext(**kwargs):
    empty_context = {
        'most_changing': {
            'declines': [
            ],
            'improvements': [
            ]
        },
        'top_savings': {
            'possible_top_savings_total': 0.0,
            'possible_savings': [],
            'achieved_savings': []
        },
        'worst': [
        ],
        'best': [
        ]
    }
    if 'declines' in kwargs:
        empty_context['most_changing']['declines'] = kwargs['declines']
    if 'improvements' in kwargs:
        empty_context['most_changing']['improvements'] = (
            kwargs['improvements'])
    if 'possible_top_savings_total' in kwargs:
        empty_context['top_savings']['possible_top_savings_total'] = (
            kwargs['possible_top_savings_total'])
    if 'possible_savings' in kwargs:
        empty_context['top_savings']['possible_savings'] = (
            kwargs['possible_savings'])
    if 'achieved_savings' in kwargs:
        empty_context['top_savings']['achieved_savings'] = (
            kwargs['achieved_savings'])
    if 'worst' in kwargs:
        empty_context['worst'] = kwargs['worst']
    if 'best' in kwargs:
        empty_context['best'] = kwargs['best']
    return empty_context
