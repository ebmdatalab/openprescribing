from django.contrib import messages
from django.contrib.auth import authenticate
from django.contrib.auth import login
from django.core.exceptions import PermissionDenied
from django.core.urlresolvers import reverse
from django.shortcuts import redirect
from django.shortcuts import render
from django.views.generic import ListView

from frontend.forms import BookmarkListForm
from frontend.models import SearchBookmark
from frontend.models import OrgBookmark


class BookmarkList(ListView):
    # As we're using custom context data, I'm not sure what
    # benefits using a ListView brings us
    context_object_name = 'bookmark_list'
    template_name = 'bookmarks/bookmark_list.html'
    model = SearchBookmark

    def post(self, request, *args, **kwargs):
        count = 0
        if request.POST.get('unsuball'):
            org_bookmarks = [x.id for x in self._org_bookmarks()]
            search_bookmarks = [x.id for x in self._search_bookmarks()]
        else:
            org_bookmarks = request.POST.getlist('org_bookmarks')
            search_bookmarks = request.POST.getlist('search_bookmarks')
        for b in org_bookmarks:
            OrgBookmark.objects.get(pk=b).delete()
            count += 1
        for b in search_bookmarks:
            SearchBookmark.objects.get(pk=b).delete()
            count += 1
        if count > 0:
            msg = "Unsubscribed from %s alert" % count
            if count > 1:
                msg += "s"
            messages.success(
                request,
                msg)
        return redirect(
            reverse('bookmark-list'))

    def _search_bookmarks(self):
        return SearchBookmark.objects.filter(
            user__id=self.request.user.id, approved=True)

    def _org_bookmarks(self):
        return OrgBookmark.objects.filter(
            user__id=self.request.user.id, approved=True)

    def get_context_data(self):
        search_bookmarks = self._search_bookmarks()
        org_bookmarks = self._org_bookmarks()
        form = BookmarkListForm(
            org_bookmarks=org_bookmarks,
            search_bookmarks=search_bookmarks
        )
        count = search_bookmarks.count() + org_bookmarks.count()
        single_bookmark = None
        if count == 1:
            single_bookmark = search_bookmarks.first() or org_bookmarks.first()
        return {
            'search_bookmarks': search_bookmarks,
            'org_bookmarks': org_bookmarks,
            'form': form,
            'count': count,
            'single_bookmark': single_bookmark
        }


def login_from_key(request, key):
    user = authenticate(key=key)
    if user:
        login(request, user)
    else:
        raise PermissionDenied
    return redirect('bookmark-list')


def email_verification_sent(request):
    sent_in_session = request.session.get('sent_in_session', 0)
    request.session['sent_in_session'] = sent_in_session + 1
    context = {'sent_in_session': sent_in_session}
    return render(request, 'account/verification_sent.html', context)
