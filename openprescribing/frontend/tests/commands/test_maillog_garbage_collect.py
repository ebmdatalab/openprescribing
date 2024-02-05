# -*- coding: utf-8 -*-
from datetime import datetime, timedelta

from django.core.management import call_command
from django.test import TestCase
from frontend.models import EmailMessage, EventType, MailLog


class MailLogGarbageCollectTest(TestCase):
    def test_maillog_garbage_collect(self):
        # Make some EmailMessages and MailLog entries of the appropriate age
        for days_ago in [0, 40, 80, 120]:
            timestamp = datetime.fromisoformat("2023-12-20T00:00:00Z") - timedelta(
                days=days_ago
            )
            recipient = f"{days_ago}_days_ago@example.com"
            message = EmailMessage.objects.create(
                message_id=f"{days_ago}_days_ago",
                to=[recipient],
            )
            # Can't set this in `create()` becaause the field is configured with `auto_now_add`
            message.created_at = timestamp
            message.save()
            MailLog.objects.create(
                timestamp=timestamp,
                recipient=recipient,
                message=message,
                event_type=EventType.SENT,
            )
            MailLog.objects.create(
                timestamp=timestamp,
                recipient=recipient,
                message=message,
                event_type=EventType.DELIVERED,
            )
            # Create a MailLog entry which isn't associated with an EmailMessage
            MailLog.objects.create(
                timestamp=timestamp,
                recipient=recipient,
                event_type=EventType.BOUNCED,
            )

        call_command("maillog_garbage_collect")

        remaining_messages = EmailMessage.objects.values_list("message_id", flat=True)
        remaining_recipients = MailLog.objects.values_list("recipient", flat=True)
        self.assertEqual(
            set(remaining_messages),
            {"0_days_ago", "40_days_ago"},
        )
        self.assertEqual(
            set(remaining_recipients),
            {"0_days_ago@example.com", "40_days_ago@example.com"},
        )

    def test_maillog_garbage_collect_handles_empty_database(self):
        self.assertEqual(EmailMessage.objects.count(), 0)
        call_command("maillog_garbage_collect")
