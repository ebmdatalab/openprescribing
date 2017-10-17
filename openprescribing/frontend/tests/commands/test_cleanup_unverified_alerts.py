from datetime import datetime

from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone

from frontend.models import OrgBookmark
from frontend.models import SearchBookmark
from frontend.models import User

import pytz


class CommandsTestCase(TestCase):
    fixtures = ['bookmark_alerts']

    def setUp(self):
        self.approved_orgbookmark_count = OrgBookmark.objects.filter(
            approved=True).count()
        self.unapproved_orgbookmark_count = OrgBookmark.objects.filter(
            approved=False).count()
        self.approved_searchbookmark_count = SearchBookmark.objects.filter(
            approved=True).count()
        self.unapproved_searchbookmark_count = SearchBookmark.objects.filter(
            approved=False).count()
        self.approved_count = (self.approved_orgbookmark_count +
                               self.approved_searchbookmark_count)
        self.unapproved_count = (self.unapproved_orgbookmark_count +
                                 self.unapproved_searchbookmark_count)

    def test_old_unapproved_bookmarks_deleted(self):
        # The fixtures contain one unapproved bookmark
        self.assertEqual(OrgBookmark.objects.count(),
                         self.approved_orgbookmark_count +
                         self.unapproved_orgbookmark_count)
        self.assertEqual(SearchBookmark.objects.count(),
                         self.approved_searchbookmark_count +
                         self.unapproved_searchbookmark_count)
        call_command('cleanup_unverified_alerts')
        self.assertEqual(OrgBookmark.objects.count(),
                         self.approved_orgbookmark_count)
        self.assertEqual(SearchBookmark.objects.count(),
                         self.approved_searchbookmark_count)

    def test_new_unapproved_bookmarks_not_deleted(self):
        old_count = OrgBookmark.objects.count()
        new_bookmark = OrgBookmark.objects.filter(approved=False).first()
        new_bookmark.created_at = timezone.now()
        new_bookmark.save()
        call_command('cleanup_unverified_alerts')
        self.assertEqual(OrgBookmark.objects.count(), old_count)

    def test_old_unverified_users_without_bookmarks_deleted(self):
        user = self._makeUser(
            has_bookmarks=False,
            date_joined=datetime(2000, 1, 1, tzinfo=pytz.utc),
            is_superuser=False,
            verified=False)
        call_command('cleanup_unverified_alerts')
        with self.assertRaises(User.DoesNotExist):
            User.objects.get(username=user.username)

    def test_old_unverified_users_with_bookmarks_not_deleted(self):
        user = self._makeUser(
            has_bookmarks=True,
            date_joined=datetime(2000, 1, 1, tzinfo=pytz.utc),
            is_superuser=False,
            verified=False)
        call_command('cleanup_unverified_alerts')
        User.objects.get(username=user.username)  # should not fail

    def test_new_unverified_users_without_bookmarks_not_deleted(self):
        user = self._makeUser(
            has_bookmarks=False,
            date_joined=timezone.now(),
            is_superuser=False,
            verified=False)
        call_command('cleanup_unverified_alerts')
        User.objects.get(username=user.username)  # should not fail

    def test_admin_users_never_deleted(self):
        user = self._makeUser(
            has_bookmarks=False,
            date_joined=datetime(2000, 1, 1, tzinfo=pytz.utc),
            is_superuser=True,
            verified=True)
        call_command('cleanup_unverified_alerts')
        User.objects.get(username=user.username)  # should not fail

    def test_verified_users_never_deleted(self):
        user = self._makeUser(
            has_bookmarks=False,
            date_joined=datetime(2000, 1, 1, tzinfo=pytz.utc),
            is_superuser=False,
            verified=True)
        call_command('cleanup_unverified_alerts')
        User.objects.get(username=user.username)  # should not fail

    def _makeUser(self,
                  has_bookmarks=True,
                  date_joined=None,
                  is_superuser=None,
                  verified=None):
        if has_bookmarks:
            user = User.objects.get(username='bookmarks-user')
        else:
            user = User.objects.get(username='no-bookmarks-user')
        if date_joined is not None:
            user.date_joined = date_joined
        if is_superuser is not None:
            user.is_superuser = is_superuser
        if verified is not None:
            confirmation = user.emailaddress_set.first()
            confirmation.verified = verified
            confirmation.save()
        user.save()
        return user
