"""
Send alerts about about NCSO concessions.
"""

import datetime
import logging

from common.alert_utils import EmailErrorDeferrer
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

    for bookmark in bookmarks:
        with EmailErrorDeferrer() as error_deferrer:
            error_deferrer.try_email(send_alert, bookmark, date)

    print("Sent {} alerts".format(bookmarks.count()))


def get_unsent_bookmarks(date):
    """Find unsent bookmarks for given date.

    Alerts should only be sent to active users.
    """

    return NCSOConcessionBookmark.objects.filter(user__is_active=True).exclude(
        user__emailmessage__tags__contains=["ncso_concessions", date]
    )


def send_alert(bookmark, date):
    """Send alert for bookmark for given date."""

    try:
        msg = bookmark_utils.make_ncso_concession_email(bookmark, tag=date)
        msg = EmailMessage.objects.create_from_message(msg)
        msg.send()
        logger.info("Sent concession alert to %s about %s" % (msg.to, bookmark.id))
    except bookmark_utils.BadAlertImageError as e:
        logger.exception(e)
