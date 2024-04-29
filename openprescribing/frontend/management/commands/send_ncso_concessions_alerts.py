"""
Send alerts about about NCSO concessions.
"""

import datetime
import logging
import sys

from django.core.management import BaseCommand
from frontend.models import EmailMessage, NCSOConcessionBookmark
from frontend.views import bookmark_utils

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = __doc__

    def add_arguments(self, parser):
        parser.add_argument("--date", help="Date that concessions were imported")

    def handle(self, *args, **options):
        date = options["date"] or datetime.date.today().strftime("%Y-%m-%d")
        send_alerts(date)


def send_alerts(date):
    """Send unsent alerts for given date."""

    bookmarks = get_unsent_bookmarks(date)

    success_count = 0
    error_count = 0
    for bookmark in bookmarks:
        description = f"to {bookmark.user.email} about {bookmark.entity_cased_name}"
        try:
            send_alert(bookmark, date)
            success_count += 1
            log_info(f"Sent bookmark {description}")
        except Exception as e:
            error_count += 1
            log_exception(f"Error sending bookmark {description}", e)

    print(f"Sent {success_count} alerts and encountered {error_count} errors")


def get_unsent_bookmarks(date):
    """Find unsent bookmarks for given date.

    Alerts should only be sent to active users.
    """

    return NCSOConcessionBookmark.objects.filter(user__is_active=True).exclude(
        user__emailmessage__tags__contains=["ncso_concessions", date]
    )


def send_alert(bookmark, date):
    """Send alert for bookmark for given date."""
    msg = bookmark_utils.make_ncso_concession_email(bookmark, tag=date)
    msg = EmailMessage.objects.create_from_message(msg)
    msg.send()


def log_info(msg):
    logger.info(msg)
    print(msg, file=sys.stderr)


def log_exception(msg, exc):
    logger.exception(exc)
    print(msg, file=sys.stderr)
    print(str(exc), file=sys.stderr)
