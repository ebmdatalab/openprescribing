from urllib import unquote

from django.contrib import messages
from django.contrib.auth import authenticate
from django.contrib.auth import login
from django.core.exceptions import PermissionDenied
from django.core.urlresolvers import reverse
from django.http import HttpResponse
from django.shortcuts import redirect
from django.shortcuts import render
from django.views.generic import ListView

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


def email_verification_sent(request):
    sent_in_session = request.session.get('sent_in_session', 0)
    request.session['sent_in_session'] = sent_in_session + 1
    context = {'sent_in_session': sent_in_session}
    return render(request, 'account/verification_sent.html', context)


def _convert_images_to_data_uris(html, images):
    for image in images:
        img_id = image['Content-ID'][1:-1]  # strip braces
        data_uri = "data:image/png;base64,%s" % (
            image.get_payload().replace("\n", ""))
        html = html.replace("cid:%s" % img_id, data_uri)
    return html


def _authenticate_possibly_new_user(email):
    try:
        user = User.objects.get(username=email)
    except User.DoesNotExist:
        user = User.objects.create_user(
            username=email, email=email)
    return authenticate(key=user.profile.key)


def _unapprove_bookmarks_when_different_user(user, request):
    # An unverified account can only create unapproved bookmarks.
    # When an account is verified, all its bookmarks are
    # approved. Whenever someone tries to add a bookmark for
    # someone else's email address (or they're not logged in),
    # that email address is marked as unverified again.  In this
    # way we can allow people who remain logged in to add several
    # alerts without having to reconfirm by email.
    emailaddress = EmailAddress.objects.filter(user=user)
    approved = False
    if user == request.user:
        approved = emailaddress.filter(
            verified=True).exists()
    else:
        approved = False
        emailaddress.update(verified=False)
    return approved


def _force_login_and_redirect(request, user):
    """Force a new login.

    This allows us to piggy-back on built-in redirect mechanisms,
    deriving from both django's built-in auth system, and
    django-allauth:

      * Users that have never been verified are redirected to
       `verification_sent.html` (thanks to django-allauth)

      * Verified users are sent to `finalise_signup.html` (per
        Django's LOGIN_REDIRECT_URL setting).

    """
    if hasattr(request, 'user'):
        # Log the user out. We don't use Django's built-in logout
        # mechanism because that clears the entire session, too,
        # and we want to know if someone's logged in previously in
        # this session.
        request.user = AnonymousUser()
        for k in [SESSION_KEY, BACKEND_SESSION_KEY, HASH_SESSION_KEY]:
            if k in request.session:
                del(request.session[k])
    return perform_login(
        request, user,
        app_settings.EmailVerificationMethod.MANDATORY,
        signup=True)


def _make_bookmark_args(user, form, subject_field_ids):
    """Construct a dict of cleaned keyword args suitable for creating a
    new bookmark
    """
    form_args = {'user': user}
    for field in subject_field_ids:
        form_args[field] = form.cleaned_data[field]
    return form_args


def _entity_type_from_object(entity):
    """Given either a PCT or Practice, return a string indicating its type
    for use in bookmark query filters that reference pct/practice
    foreign keys

    """
    if isinstance(entity, PCT):
        return 'pct'
    elif isinstance(entity, Practice):
        return 'practice'
    else:
        raise RuntimeError("Entity must be Practice or PCT")


def _signed_up_for_alert(request, entity):
    if request.user.is_authenticated():
        q = {_entity_type_from_object(entity): entity}
        signed_up_for_alert = bool(
            request.user.orgbookmark_set.filter(**q))
    else:
        signed_up_for_alert = False
    return signed_up_for_alert


def _bookmark_and_newsletter_form(request, entity):
    """Build a form for newsletter/alert signups, and handle user login
    for POSTs to that form.
    """
    entity_type = _entity_type_from_object(entity)
    if request.method == 'POST':
        form = _handle_bookmark_and_newsletter_post(
            request,
            OrgBookmark,
            OrgBookmarkForm,
            entity_type)
    else:
        form = OrgBookmarkForm(
            initial={entity_type: entity.pk,
                     'email': getattr(request.user, 'email', '')})
    return form


def _handle_bookmark_and_newsletter_post(
        request, subject_class,
        subject_form_class,
        *subject_field_ids):
    """Handle search/org bookmark and newsletter signup form:

    * create a search or org bookmark
    * annotate the user's session (because newsletter signup can be
      multi-stage)
    * redirect to confirmation and/or newsletter signup page.

    """
    form = subject_form_class(request.POST)
    if form.is_valid():
        email = form.cleaned_data['email']
        if 'newsletter' in form.cleaned_data['newsletters']:
            # add a session variable. Then handle it in the next page,
            # which is either the verification page, or a dedicated
            # "tell us a bit more" page.
            request.session['newsletter_email'] = email
        if 'alerts' in form.cleaned_data['newsletters']:
            request.session['alerts_requested'] = 1
            user = _authenticate_possibly_new_user(email)
            form_args = _make_bookmark_args(user, form, subject_field_ids)
            form_args['approved'] = _unapprove_bookmarks_when_different_user(
                user, request)
            subject_class.objects.get_or_create(**form_args)
            return _force_login_and_redirect(request, user)
        else:
            return redirect('newsletter-signup')
    return form
