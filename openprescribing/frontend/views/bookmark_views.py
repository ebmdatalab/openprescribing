from django.contrib import messages
from django.core.urlresolvers import reverse
from django.shortcuts import get_object_or_404, redirect, render

from frontend.forms import BookmarkListForm
from frontend.models import Profile


def bookmarks(request, key):
    user = _get_user_by_key_or_404(key)

    search_bookmarks = user.searchbookmark_set.all()
    org_bookmarks = user.orgbookmark_set.all()
    ncso_concessions_bookmarks = user.ncsoconcessionbookmark_set.all()

    if request.method == "POST":
        if not request.POST.get("unsuball"):
            org_bookmarks = org_bookmarks.filter(
                pk__in=request.POST.getlist("org_bookmarks")
            )
            search_bookmarks = search_bookmarks.filter(
                pk__in=request.POST.getlist("search_bookmarks")
            )
            ncso_concessions_bookmarks = ncso_concessions_bookmarks.filter(
                pk__in=request.POST.getlist("ncso_concessions_bookmarks")
            )

        # QuerySet.delete() returns a tuple whose first element is the number
        # of records deleted.
        count = (
            org_bookmarks.delete()[0]
            + search_bookmarks.delete()[0]
            + ncso_concessions_bookmarks.delete()[0]
        )

        if count > 0:
            msg = "Unsubscribed from %s alert" % count
            if count > 1:
                msg += "s"
            messages.success(request, msg)

        return redirect(reverse("bookmarks", args=[key]))

    form = BookmarkListForm(
        org_bookmarks=org_bookmarks,
        search_bookmarks=search_bookmarks,
        ncso_concessions_bookmarks=ncso_concessions_bookmarks,
    )
    count = (
        search_bookmarks.count()
        + org_bookmarks.count()
        + ncso_concessions_bookmarks.count()
    )

    if count == 1:
        single_bookmark = (
            search_bookmarks.first()
            or org_bookmarks.first()
            or ncso_concessions_bookmarks.first()
        )
    else:
        single_bookmark = None

    ctx = {
        "search_bookmarks": search_bookmarks,
        "org_bookmarks": org_bookmarks,
        "ncso_concessions_bookmarks": ncso_concessions_bookmarks,
        "form": form,
        "count": count,
        "single_bookmark": single_bookmark,
    }

    return render(request, "bookmarks/bookmark_list.html", ctx)


def _get_user_by_key_or_404(key):
    profile = get_object_or_404(Profile, key=key)
    return profile.user
