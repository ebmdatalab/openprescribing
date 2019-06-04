'''
Send alerts about all of NHS England
'''

from __future__ import print_function

import logging

from django.core.management import BaseCommand

from common.alert_utils import EmailErrorDeferrer
from frontend.models import EmailMessage, OrgBookmark, User, Profile, ImportLog
from frontend.views import bookmark_utils

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = __doc__

    def add_arguments(self, parser):
        parser.add_argument(
            '--recipient-email',
            help='Send example email to this address'
        )

    def handle(self, recipient_email=None, **options):
        send_alerts(recipient_email=recipient_email)


def send_alerts(recipient_email=None):
    '''Send unsent alerts for the current month'''

    date = (
        ImportLog.objects
        .latest_in_category('prescribing')
        .current_at
        .strftime('%Y-%m-%d')
        .lower()
    )

    if recipient_email is None:
        bookmarks = get_unsent_bookmarks(date)
    else:
        bookmarks = [make_dummy_bookmark(recipient_email)]

    for bookmark in bookmarks:
        with EmailErrorDeferrer() as error_deferrer:
            error_deferrer.try_email(
                send_alert,
                bookmark,
                date
            )

    print('Sent {} alerts'.format(len(bookmarks)))


def make_dummy_bookmark(email_address):
    '''Make a dummy bookmark with this email address for testing purposes'''
    dummy_user = User(email=email_address, id='dummyid')
    dummy_user.profile = Profile(key='dummykey')
    return OrgBookmark(
        user=dummy_user,
        pct_id=None,
        practice_id=None
    )


def get_unsent_bookmarks(date):
    '''Find unsent bookmarks for given date.

    Alerts should only be sent to active users who have an approved bookmark.
    '''

    return OrgBookmark.objects.filter(
        practice__isnull=True,
        pct__isnull=True,
        approved=True,
        user__is_active=True
    ).exclude(
        user__emailmessage__tags__contains=['all_england', date]
    )


def send_alert(bookmark, date):
    '''Send alert for bookmark for given date.'''
    try:
        message = bookmark_utils.make_all_england_email(bookmark, tag=date)
        email_message = EmailMessage.objects.create_from_message(message)
        email_message.send()
        logger.info('Sent alert to %s about %s', email_message.to, bookmark.name)
    except bookmark_utils.BadAlertImageError as e:
        logger.exception(e)
