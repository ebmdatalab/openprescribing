# -*- coding: utf-8 -*-
import base64
from datetime import date
from datetime import datetime
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import re
import socket
from threading import Thread

import requests
from mock import patch
from mock import ANY

from django.core.mail import EmailMultiAlternatives
from django.test import TestCase
from django.conf import settings
from frontend.models import OrgBookmark
from frontend.models import SearchBookmark
from frontend.models import User
from frontend.models import Measure
from frontend.management.commands.send_monthly_org_alerts import Command


class AnyStringWith(str):
    def __eq__(self, other):
        return self in other


class GetBookmarksTestCase(TestCase):
    fixtures = ['bookmark_alerts']

    def test_get_bookmarks_without_options(self):
        bookmarks = Command().get_bookmarks()
        active = all([x.user.is_active for x in bookmarks])
        self.assertEqual(len(bookmarks), 3)
        self.assertTrue(active)

    def test_get_bookmarks_with_options(self):
        bookmarks = Command().get_bookmarks(
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


@patch('frontend.views.bookmark_utils.InterestingMeasureFinder')
@patch('frontend.management.commands.send_monthly_org_alerts.EmailMultiAlternatives')
@patch.object(Command, 'attach_image')
class SendEmailTestCase(TestCase):
    fixtures = ['bookmark_alerts', 'measures']

    def _makeContext(self, **kwargs):
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

    def test_email_recipient(self, attach_image, email, finder):
        test_context = self._makeContext()
        finder.return_value.context_for_org_email.return_value = test_context
        Command().handle(recipient_email='s@s.com',
                         ccg='03V',
                         practice='P87629')
        email.assert_any_call(
            ANY,  # subject
            ANY,  # body
            "hello@openprescribing.net",
            ['s@s.com']
        )
        email.return_value.send.assert_any_call()

    def test_email_body_no_data(self, attach_image, email, finder):
        test_context = self._makeContext()
        finder.return_value.context_for_org_email.return_value = test_context
        Command().handle(recipient_email='s@s.com',
                         ccg='03V',
                         practice='P87629')
        attachment = email.return_value.attach_alternative
        # Name of the practice
        attachment.assert_called_once_with(
            AnyStringWith('1/ST ANDREWS MEDICAL PRACTICE'), 'text/html')
        # Unsubscribe link
        attachment.assert_called_once_with(
            AnyStringWith('/bookmarks/dummykey'), 'text/html')

        attachment.assert_called_once_with(
            AnyStringWith("This month, there's nothing to tell"), 'text/html')

    def test_email_body_declines(self, attach_image, email, finder):
        measure = Measure.objects.get(pk='cerazette')
        test_context = self._makeContext(declines=[(measure, 99.92, 0.12, 10.002)])
        finder.return_value.context_for_org_email.return_value = test_context
        attach_image.return_value = 'unique-image-id'
        Command().handle(recipient_email='s@s.com',
                         ccg='03V',
                         practice='P87629')
        attachment = email.return_value.attach_alternative
        attachment.assert_called_once_with(
            AnyStringWith("You've slipped on"), 'text/html')

        body = attachment.call_args[0][0]
        self.assertIn("We've found some areas for you to look at", body)
        self.assertRegexpMatches(
            body, '<a href="/practice/P87629/measures/cerazette/".*>'
            "Cerazette vs. Desogestrel</a> - you've gone from the 100th "
            "centile to the 0th centile over the past 9 months")
        self.assertIn('<img src="cid:unique-image-id', body)
        self.assertNotIn("Your best prescribing areas", body)
        self.assertNotIn("Cost savings", body)

    def test_email_body_worst(self, attach_image, email, finder):
        measure = Measure.objects.get(pk='cerazette')
        test_context = self._makeContext(worst=[measure])
        finder.return_value.context_for_org_email.return_value = test_context
        attach_image.return_value = 'unique-image-id'
        Command().handle(recipient_email='s@s.com',
                         ccg='03V',
                         practice='P87629')
        attachment = email.return_value.attach_alternative
        attachment.assert_called_once_with(
            AnyStringWith("Ongoing areas for concern"), 'text/html')

        body = attachment.call_args[0][0]
        self.assertIn("We've found some areas for you to look at", body)
        self.assertRegexpMatches(
            body, re.compile(
                'the worst 10% of.*practices for.*<a href="/practice/P87629'
                '/measures/cerazette/".*>'
                "Cerazette vs. Desogestrel</a>", re.DOTALL))
        self.assertIn('<img src="cid:unique-image-id', body)

    def test_email_body_two_savings(self, attach_image, email, finder):
        measure = Measure.objects.get(pk='cerazette')
        test_context = self._makeContext(possible_savings=[
            (measure, 9.9), (measure, 1.12)])
        finder.return_value.context_for_org_email.return_value = test_context
        attach_image.return_value = 'unique-image-id'
        Command().handle(recipient_email='s@s.com',
                         ccg='03V',
                         practice='P87629')
        attachment = email.return_value.attach_alternative
        body = attachment.call_args[0][0]
        self.assertIn(
            "These add up to £11 of potential savings".decode('utf-8'),
            body)
        self.assertRegexpMatches(
            body, '<li.*>£10 on <a href="/practice/P87629'
            '/measures/cerazette/".*>'
            "Cerazette vs. Desogestrel</a>".decode('utf-8'))

    def test_email_body_one_saving(self, attach_image, email, finder):
        measure = Measure.objects.get(pk='cerazette')
        test_context = self._makeContext(possible_savings=[
            (measure, 9.9)])
        finder.return_value.context_for_org_email.return_value = test_context
        Command().handle(recipient_email='s@s.com',
                         ccg='03V',
                         practice='P87629')
        attachment = email.return_value.attach_alternative
        body = attachment.call_args[0][0]
        self.assertIn(
            "If you had prescribed in line with the average practice",
            body)
        self.assertRegexpMatches(
            body, 'you could have saved £10 on <a href="/practice/P87629'
            '/measures/cerazette/".*>'
            "Cerazette vs. Desogestrel</a>".decode('utf-8'))

    def test_email_body_total_savings(self, attach_image, email, finder):
        test_context = self._makeContext(possible_top_savings_total=9000.1)
        finder.return_value.context_for_org_email.return_value = test_context
        Command().handle(recipient_email='s@s.com',
                         ccg='03V',
                         practice='P87629')
        attachment = email.return_value.attach_alternative
        body = attachment.call_args[0][0]
        self.assertIn(
            "you could save around <b>£9,000</b>".decode('utf-8'),
            body)

class MockServerRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/page.html':
            self.send_response(requests.codes.ok)
            self.send_header('Content-Type', 'text/html')
            self.end_headers()
            response_content = """
            <html>
            <head><script src='/jquery.min.js'></script></head>
            <div id='thing1'>This is thing 1</div>
            <div id='thing2'>This is thing 2</div>
            """
            self.wfile.write(response_content)
            return
        elif self.path == '/jquery.min.js':
            self.send_response(requests.codes.ok)
            self.send_header('Content-Type', 'text/javascript')
            self.end_headers()
            with open(settings.SITE_ROOT + '/media/js/'
                      'node_modules/jquery/dist/jquery.min.js', 'r') as f:
                self.wfile.write(f.read())
                return


def get_free_port():
    s = socket.socket(socket.AF_INET, type=socket.SOCK_STREAM)
    s.bind(('localhost', 0))
    address, port = s.getsockname()
    s.close()
    return port


def start_mock_server(port):
    mock_server = HTTPServer(('localhost', port), MockServerRequestHandler)
    mock_server_thread = Thread(target=mock_server.serve_forever)
    mock_server_thread.setDaemon(True)
    mock_server_thread.start()


class GenerateImageTestCase(unittest.TestCase):
    def test_image_generated(self):
        port = get_free_port()
        start_mock_server(port)
        msg = EmailMultiAlternatives(
            "Subject", "body", "sender@email.com", ["recipient@email.com"])
        url = ":%s/page.html" % port
        file_path = "/tmp/image.png"
        selector = "#thing2"
        self.assertEqual(len(msg.attachments), 0)
        image = Command().attach_image(msg, url, file_path, selector)
        with open(
                settings.SITE_ROOT + '/frontend/tests/fixtures/'
                'alert-email-image.png', 'rb') as expected:
            self.assertEqual(len(msg.attachments), 1)
            attachment = msg.attachments[0]
            # Check the attachment is as we expect
            self.assertEqual(attachment.get_filename(), 'image.png')
            self.assertIn(image, attachment['Content-ID'])
            # Attachments in emails are base64 *with line breaks*, so
            # we remove those.
            self.assertEqual(
                attachment.get_payload().replace("\n", ""),
                base64.b64encode(expected.read()))
