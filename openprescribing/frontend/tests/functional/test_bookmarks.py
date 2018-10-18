# -*- coding: utf-8 -*-
import unittest

from django.core.urlresolvers import reverse

from selenium_base import SeleniumTestCase

from frontend.models import User, OrgBookmark


class BookmarksTest(SeleniumTestCase):
    fixtures = ['bookmark_alerts', 'bookmark_alerts_extra']

    def _get_bookmark_url_for_user(self, username='bookmarks-user'):
        key = User.objects.get(username=username).profile.key
        return reverse('bookmark-login', kwargs={'key': key})

    def test_unsubscribe_from_one_alert(self):
        url = self._get_bookmark_url_for_user()
        bookmark_count = OrgBookmark.objects.count()
        self.browser.get(self.live_server_url + url)
        self.find_by_xpath("//input[@name='org_bookmarks']").click()
        self.find_by_xpath("//input[@value='Unsubscribe']").click()
        self.find_by_xpath("//div[contains(text(), 'Unsubscribed')]")
        self.assertEqual(OrgBookmark.objects.count(), bookmark_count - 1)

    def test_unsubscribe_all_at_once(self):
        url = self._get_bookmark_url_for_user()
        bookmark_count = OrgBookmark.objects.count()
        self.browser.get(self.live_server_url + url)
        self.find_by_xpath("//input[@value='Unsubscribe from all']").click()
        self.find_by_xpath("//div[contains(text(), 'Unsubscribed')]")
        self.assertEqual(OrgBookmark.objects.count(), bookmark_count - 2)

    def test_unsubscribe_all_at_once_with_single_bookmark(self):
        # The form used if you have only a single subscription is different
        # from the form for multliple subscriptions so we have to test it
        # separately
        url = self._get_bookmark_url_for_user(username='single-bookmark-user')
        bookmark_count = OrgBookmark.objects.count()
        self.browser.get(self.live_server_url + url)
        self.find_by_xpath("//input[@value='Unsubscribe']").click()
        self.find_by_xpath("//div[contains(text(), 'Unsubscribed')]")
        self.assertEqual(OrgBookmark.objects.count(), bookmark_count - 1)


if __name__ == '__main__':
    unittest.main()
