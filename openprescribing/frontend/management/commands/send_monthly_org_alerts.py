# -*- coding: utf-8 -*-

import logging

from django.core.management.base import BaseCommand
from django.core.management.base import CommandError
from frontend.models import OrgBookmark
from frontend.models import Profile
from frontend.models import SearchBookmark
from frontend.models import User

from frontend.views import bookmark_utils

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    args = ''
    help = ''' Send monthly emails based on bookmarks. With no arguments, sends
    an email to every user for each of their bookmarks, for the
    current month. With arguments, sends a test email to the specified
    user for the specified organisation.'''

    def add_arguments(self, parser):
        parser.add_argument('--recipient-email')
        parser.add_argument('--ccg')
        parser.add_argument('--practice')
        parser.add_argument('--search-name')
        parser.add_argument('--url')

    def get_org_bookmarks(self, **options):
        if options['recipient_email'] and (
                options['ccg'] or options['practice']):
            dummy_user = User(email=options['recipient_email'], id='dummyid')
            dummy_user.profile = Profile(key='dummykey')
            bookmarks = [OrgBookmark(
                user=dummy_user,
                pct_id=options['ccg'],
                practice_id=options['practice']
            )]
        elif not options['recipient_email']:
            # Perhaps add a constraint here to ensure we don't send two
            # emails for one month?
            bookmarks = OrgBookmark.objects.filter(
                user__is_active=True)
        else:
            bookmarks = []
        return bookmarks

    def get_search_bookmarks(self, **options):
        if options['recipient_email'] and options['url']:
            dummy_user = User(email=options['recipient_email'], id='dummyid')
            dummy_user.profile = Profile(key='dummykey')
            bookmarks = [SearchBookmark(
                user=dummy_user,
                url=options['url'],
                name=options['search_name']
            )]
        elif not options['recipient_email']:
            bookmarks = SearchBookmark.objects.filter(
                user__is_active=True)
        else:
            bookmarks = []
        return bookmarks

    def validate_options(self, **options):
        if ((options['url'] or options['ccg'] or options['practice']) and
           not options['recipient_email']):
            raise CommandError(
                "You must specify a test recipient email if you want to "
                "specify a test CCG, practice, or URL")
        if options['url'] and (options['practice'] or options['ccg']):
            raise CommandError(
                "You must specify either a URL, or one of a ccg or a practice"
            )

    def handle(self, *args, **options):
        self.validate_options(**options)
        for org_bookmark in self.get_org_bookmarks(**options):
            stats = bookmark_utils.InterestingMeasureFinder(
                practice=org_bookmark.practice or options['practice'],
                pct=org_bookmark.pct or options['ccg']).context_for_org_email()

            msg = bookmark_utils.make_org_email(
                org_bookmark, stats)
            msg.send()
            logger.info("Sent message to user %s about bookmark %s" % (
                msg.recipients(), org_bookmark.id))
        for search_bookmark in self.get_search_bookmarks(**options):
            recipient_id = search_bookmark.user.id
            msg = bookmark_utils.make_search_email(
                search_bookmark)
            msg.send()
            logger.info("Sent message to user %s about bookmark %s" % (
                recipient_id, search_bookmark.id))
