from django.conf import settings
from django.core import mail
from django.test import TestCase

from frontend.feedback import send_feedback_mail


class FeedbackTests(TestCase):
    def test_send_feedback_mail(self):
        mail.outbox = []

        send_feedback_mail(
            user_name="Alice Apple",
            user_email_addr="alice@example.com",
            subject="An apple a day...",
            message="...keeps the doctor away",
            url="https://openprescribing.net/bnf/090603/",
        )

        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]

        expected_body = """New feedback from Alice Apple (via https://openprescribing.net/bnf/090603/)

...keeps the doctor away
"""

        self.assertEqual(email.to, [settings.SUPPORT_TO_EMAIL])
        self.assertEqual(email.from_email, "Alice Apple <alice@example.com>")
        self.assertEqual(email.reply_to, ["alice@example.com"])
        self.assertEqual(
            email.subject,
            "OpenPrescribing Feedback: An apple a day...")
        self.assertEqual(email.body, expected_body)
