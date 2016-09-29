from django.contrib import messages
from django.contrib.auth import authenticate
from django.contrib.auth import login
from django.core.exceptions import PermissionDenied
from django.core.urlresolvers import reverse
from django.shortcuts import redirect
from django.views.generic import ListView

from frontend.forms import BookmarkListForm
from frontend.models import Measure, MeasureGlobal, MeasureValue
from frontend.models import SearchBookmark, OrgBookmark


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
            user__id=self.request.user.id)

    def _org_bookmarks(self):
        return OrgBookmark.objects.filter(
            user__id=self.request.user.id)

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


def org_alert_email_context(org_bookmark):
    """Given an org, generate a context to be used when composing monthly
    alerts.

    Not a true Django view, but feels appropriate to store it with
    other views."""
    org = org_bookmark.pct

    # Where they're in the worst decile over the past six months,
    # ordered by badness

    worst_measures = []
    for measure in Measure.objects.all():
        percentiles = MeasureGlobal.objects.filter(
            measure=measure, month__gte='2012-01-01'
        ).only('month', 'percentiles')
        bad_count_threshold = percentiles.count()
        print
        print "Found %s thresholds" % bad_count_threshold
        print "Looking at %s for CCG %s" % (measure, org.code)
        if measure.low_is_good:
            for p in percentiles:
                print "Bad means more than %s on %s"% (p.percentiles['ccg']['90'], p.month)
                is_worst = MeasureValue.objects.filter(
                    measure=measure, pct=org, practice=None,
                    percentile__gte=p.percentiles['ccg']['90'] * 100,
                    month=p.month
                )
                if is_worst.count() == 0:
                    worst_measures = []
                    break
                else:
                    print "Worse on following dates"
                    print [(x.month, x.percentile) for x in is_worst]
                    worst_measures.append(measure)
        else:
            for p in percentiles:
                is_worst = MeasureValue.objects.filter(
                    measure=measure,
                    pct=org, practice=None,
                    percentile__lte=p.percentiles['ccg']['10'] * 100,
                    month=p.month
                )
                if is_worst.count() == 0:
                    worst_measures = []
                    break
                else:
                    worst_measures.append(measure)

    # Where they're in the top 10% over the past six months, ordered by badness
    best_measures = []

    # Where they've slipped more than N centiles over period Y, overed
    # by most slippage. A triple of (slippage_from, slippage_to,
    # mesaure_id)
    fastest_worsening_measures = [()]

    # Top savings for CCG, where savings are greater than GBP1000 .
    top_savings = []

    total_possible_savings = 0
    return {
        'worst_measures': worst_measures,
        'best_measures': best_measures,
        'fastest_worsening_measures': fastest_worsening_measures,
        'top_savings': top_savings,
        'total_possible_savings': total_possible_savings}
