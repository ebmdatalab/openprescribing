from django.test import TestCase
from django.core.urlresolvers import reverse

from frontend.models import User


class TestBookmarkViews(TestCase):
    fixtures = ["bookmark_alerts", "bookmark_alerts_extra"]

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.get(username="bookmarks-user")
        cls.url = reverse("bookmarks", kwargs={"key": cls.user.profile.key})

    def test_list_bookmarks(self):
        response = self.client.get(self.url, follow=True)
        self.assertContains(
            response, "You are currently subscribed to 4 monthly alerts"
        )

    def test_list_bookmarks_invalid_key(self):
        url = reverse("bookmarks", kwargs={"key": "broken"})
        response = self.client.get(url, follow=True)
        self.assertEqual(response.status_code, 404)

    def test_unsubscribe_from_some(self):
        data = {
            "org_bookmarks": [self.user.orgbookmark_set.first().pk],
            "search_bookmarks": [self.user.searchbookmark_set.first().pk],
        }
        response = self.client.post(self.url, data, follow=True)
        self.assertContains(response, "Unsubscribed from 2 alerts")
        self.assertEqual(self.user.orgbookmark_set.count(), 2)
        self.assertEqual(self.user.searchbookmark_set.count(), 0)

    def test_unsubscribe_from_all(self):
        data = {"unsuball": 1}
        response = self.client.post(self.url, data, follow=True)
        self.assertContains(response, "Unsubscribed from 4 alerts")
        self.assertEqual(self.user.orgbookmark_set.count(), 0)
        self.assertEqual(self.user.searchbookmark_set.count(), 0)
