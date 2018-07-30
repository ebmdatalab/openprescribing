import base64
from mock import patch

from django.test import TransactionTestCase
from django.core.urlresolvers import reverse

from frontend.models import OrgBookmark
from frontend.models import SearchBookmark
from frontend.models import PCT
from frontend.models import Practice
from frontend.models import User
from frontend.models import Measure


class TestBookmarkViews(TransactionTestCase):
    fixtures = ['bookmark_alerts']

    def _get_bookmark_url_for_user(self):
        key = User.objects.get(username='bookmarks-user').profile.key
        return reverse('bookmark-login', kwargs={'key': key})

    def test_list_bookmarks_not_logged_in(self):
        response = self.client.get(reverse('bookmark-list'))
        self.assertContains(response, "You are not subscribed to any alerts")

    def test_list_bookmarks_logged_in(self):
        url = self._get_bookmark_url_for_user()
        response = self.client.get(url, follow=True)
        self.assertContains(
            response, "You are currently subscribed to 3 monthly alerts")

    def test_list_bookmarks_invalid_key(self):
        url = reverse('bookmark-login', kwargs={'key': 'broken'})
        response = self.client.get(url, follow=True)
        self.assertEqual(response.status_code, 403)

    def test_unsubscribe_one_by_one(self):
        # First, log in
        url = self._get_bookmark_url_for_user()
        self.client.get(url, follow=True)
        # There should be 2 bookmarks to get rid of
        for _ in range(3):
            data = {'org_bookmarks': [OrgBookmark.objects.first().pk]}
            response = self.client.post(
                reverse('bookmark-list'), data, follow=True)
            self.assertContains(
                response,
                "Unsubscribed from 1 alert")
        self.assertEqual(OrgBookmark.objects.count(), 1)

    def test_unsubscribe_all_at_once(self):
        # First, log in
        url = self._get_bookmark_url_for_user()
        self.client.get(url, follow=True)
        data = {'unsuball': 1}
        response = self.client.post(
            reverse('bookmark-list'), data, follow=True)
        self.assertContains(
            response,
            "Unsubscribed from 3 alerts")
        # There's one org bookmark which is unapproved, so they don't
        # see it in their list, and it doesn't get deleted.
        self.assertEqual(OrgBookmark.objects.count(), 2)
