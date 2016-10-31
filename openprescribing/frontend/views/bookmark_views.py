from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.contrib.auth import authenticate
from django.contrib.auth import login
from django.core.exceptions import PermissionDenied
from django.core.urlresolvers import reverse
from django.shortcuts import redirect
from django.views.generic import ListView
from django.http import HttpResponse

from frontend.forms import BookmarkListForm
from frontend.models import SearchBookmark
from frontend.models import OrgBookmark
from frontend.models import PCT
from frontend.models import Practice
from frontend.models import Profile
from frontend.models import User
from frontend.views import bookmark_utils


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


@staff_member_required
def preview_practice_bookmark(request, code):
    return preview_bookmark(request, practice=Practice.objects.get(pk=code))


@staff_member_required
def preview_ccg_bookmark(request, code):
    return preview_bookmark(request, pct=PCT.objects.get(pk=code))


def preview_bookmark(request, practice=None, pct=None):
    context = bookmark_utils.InterestingMeasureFinder(
        practice=practice,
        pct=pct
    ).context_for_org_email()
    user = User(email='foo@foo.com')
    user.profile = Profile()
    bookmark = OrgBookmark(practice=practice, pct=pct, user=user)
    msg = bookmark_utils.make_email_html(
        bookmark, context)
    # now turn the message into html, including inlined images
    html = msg.alternatives[0][0]
    images = msg.attachments
    return HttpResponse(_convert_images_to_data_uris(html, images))

def _convert_images_to_data_uris(html, images):
    for image in images:
        img_id = image['Content-ID'][1:-1]  # strip braces
        data_uri = "data:image/png;base64,%s" % (
            image.get_payload().replace("\n", ""))
        html = html.replace("cid:%s" % img_id, data_uri)
    return html
