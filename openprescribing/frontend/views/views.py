import functools
from lxml import html
from requests.exceptions import HTTPError
from urllib import urlencode
from urlparse import urlparse, urlunparse
import hashlib
import requests
import sys

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import BACKEND_SESSION_KEY
from django.contrib.auth import HASH_SESSION_KEY
from django.contrib.auth import SESSION_KEY
from django.contrib.auth import authenticate
from django.contrib.auth.models import AnonymousUser
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.db import IntegrityError
from django.db.models import Sum
from django.http import Http404
from django.http import HttpResponse
from django.http.response import HttpResponseRedirect
from django.shortcuts import redirect
from django.shortcuts import render, get_object_or_404
from django.utils.safestring import mark_safe

from allauth.account import app_settings
from allauth.account.models import EmailAddress
from allauth.account.utils import perform_login

from common.utils import get_env_setting
from common.utils import parse_date
from dmd.models import DMDProduct
from frontend.forms import OrgBookmarkForm
from frontend.forms import SearchBookmarkForm
from frontend.models import Chemical
from frontend.models import ImportLog
from frontend.models import Measure
from frontend.models import MeasureValue
from frontend.models import MEASURE_TAGS
from frontend.models import OrgBookmark
from frontend.models import Practice, PCT, Section
from frontend.models import Presentation
from frontend.models import PPUSaving
from frontend.models import SearchBookmark

from mailchimp3 import MailChimp


class BadRequestError(Exception):
    pass


def handle_bad_request(view_function):
    @functools.wraps(view_function)
    def wrapper(request, *args, **kwargs):
        try:
            return view_function(request, *args, **kwargs)
        except BadRequestError as e:
            context = {'error_code': 400, 'reason': unicode(e)}
            return render(request, '500.html', context, status=400)
    return wrapper


##################################################
# BNF SECTIONS
##################################################
def all_bnf(request):
    sections = Section.objects.filter(is_current=True)
    context = {
        'sections': sections
    }
    return render(request, 'all_bnf.html', context)


def bnf_section(request, section_id):
    section = get_object_or_404(Section, bnf_id=section_id)
    id_len = len(section_id)
    bnf_chapter = None
    bnf_section = None
    try:
        if id_len > 2:
            bnf_chapter = Section.objects.get(bnf_id=section_id[:2])
        if id_len > 4:
            bnf_section = Section.objects.get(bnf_id=section_id[:4])
    except Section.DoesNotExist:
        pass
    chemicals = None
    subsections = Section.objects.filter(
        bnf_id__startswith=section_id,
        is_current=True
    ).extra(
        where=["CHAR_LENGTH(bnf_id)=%s" % (id_len + 2)])
    if not subsections:
        chemicals = Chemical.objects.filter(
            bnf_code__startswith=section_id,
            is_current=True
        ).order_by('chem_name')
    context = {
        'section': section,
        'bnf_chapter': bnf_chapter,
        'bnf_section': bnf_section,
        'subsections': subsections,
        'chemicals': chemicals,
        'page_id': section_id
    }
    return render(request, 'bnf_section.html', context)


##################################################
# CHEMICALS
##################################################

def all_chemicals(request):
    chemicals = Chemical.objects.filter(
        is_current=True
    ).order_by('bnf_code')
    context = {
        'chemicals': chemicals
    }
    return render(request, 'all_chemicals.html', context)


def chemical(request, bnf_code):
    c = get_object_or_404(Chemical, bnf_code=bnf_code)

    # Get BNF chapter, section etc.
    bnf_chapter = Section.objects.get(bnf_id=bnf_code[:2])
    bnf_section = Section.objects.get(bnf_id=bnf_code[:4])
    try:
        bnf_para = Section.objects.get(bnf_id=bnf_code[:6])
    except Section.DoesNotExist:
        bnf_para = None

    context = {
        'page_id': bnf_code,
        'chemical': c,
        'bnf_chapter': bnf_chapter,
        'bnf_section': bnf_section,
        'bnf_para': bnf_para
    }
    return render(request, 'chemical.html', context)


##################################################
# Price per unit
##################################################
@handle_bad_request
def price_per_unit_by_presentation(request, entity_code, bnf_code):
    date = _specified_or_last_date(request, 'ppu')
    presentation = get_object_or_404(Presentation, pk=bnf_code)
    product = presentation.dmd_product
    if len(entity_code) == 3:
        entity = get_object_or_404(PCT, code=entity_code)
    elif len(entity_code) == 6:
        entity = get_object_or_404(Practice, code=entity_code)

    query = {
        'format': 'json',
        'bnf_code': presentation.bnf_code,
        'highlight': entity.code,
        'date': date.strftime('%Y-%m-%d'),
    }

    if 'trim' in request.GET:
        query['trim'] = request.GET['trim']

    querystring = urlencode(query)

    parsed_url = urlparse(settings.API_HOST)

    bubble_data_url = urlunparse((
        parsed_url.scheme,   # scheme
        parsed_url.netloc,   # host
        '/api/1.0/bubble/',  # path
        '',                  # params
        querystring,         # query
        '',                  # fragment
    ))

    context = {
        'entity': entity,
        'highlight': entity.code,
        'highlight_name': entity.cased_name,
        'name': presentation.product_name,
        'bnf_code': presentation.bnf_code,
        'presentation': presentation,
        'product': product,
        'date': date,
        'by_presentation': True,
        'bubble_data_url': bubble_data_url,
    }
    return render(request, 'price_per_unit.html', context)


##################################################
# GP PRACTICES
##################################################

def all_practices(request):
    practices = Practice.objects.filter(setting=4).order_by('name')
    context = {
        'practices': practices
    }
    return render(request, 'all_practices.html', context)


def _specified_or_last_date(request, category):
    date = request.GET.get('date', None)
    if date:
        try:
            date = parse_date(date)
        except ValueError:
            raise BadRequestError(u'Date not in valid YYYY-MM-DD format: %s' % date)
    else:
        date = ImportLog.objects.latest_in_category(category).current_at
    return date


@handle_bad_request
def practice_price_per_unit(request, code):
    date = _specified_or_last_date(request, 'ppu')
    practice = get_object_or_404(Practice, code=code)
    context = {
        'entity': practice,
        'highlight': practice.code,
        'highlight_name': practice.cased_name,
        'date': date,
        'by_practice': True
    }
    return render(request, 'price_per_unit.html', context)


##################################################
# CCGs
##################################################

def all_ccgs(request):
    ccgs = PCT.objects.filter(
        close_date__isnull=True, org_type="CCG").order_by('name')
    context = {
        'ccgs': ccgs
    }
    return render(request, 'all_ccgs.html', context)


@handle_bad_request
def ccg_price_per_unit(request, code):
    date = _specified_or_last_date(request, 'ppu')
    ccg = get_object_or_404(PCT, code=code)
    context = {
        'entity': ccg,
        'highlight': ccg.code,
        'highlight_name': ccg.cased_name,
        'date': date,
        'by_ccg': True
    }
    return render(request, 'price_per_unit.html', context)


##################################################
# MEASURES
# These replace old CCG and practice dashboards.
##################################################

CORE_TAG = 'core'


def _get_measure_tag_filter(params, show_all_by_default=False):
    tags = params.getlist('tags')
    # Support passing a single "tags" param with a comma separated list
    tags = sum([tag.split(',') for tag in tags], [])
    tags = filter(None, tags)
    default_tags = [] if show_all_by_default else [CORE_TAG]
    if not tags:
        tags = default_tags
    try:
        tag_details = [MEASURE_TAGS[tag] for tag in tags]
    except KeyError as e:
        raise BadRequestError(u'Unrecognised tag: {}'.format(e.args[0]))
    return {
        'tags': tags,
        'names': [tag['name'] for tag in tag_details],
        'details': [tag for tag in tag_details if tag['description']],
        'show_message': (tags != default_tags),
        'all_tags': _get_tags_select_options(tags, show_all_by_default)
    }


def _get_tags_select_options(selected_tags, show_all_by_default):
    options = [
        {'id': key, 'name': tag['name'], 'selected': (key in selected_tags)}
        for (key, tag) in MEASURE_TAGS.items()
    ]
    options.sort(key=_sort_core_tag_first)
    if show_all_by_default:
        options.insert(0, {
            'id': '',
            'name': 'All Measures',
            'selected': (len(selected_tags) == 0)
        })
    return options


def _sort_core_tag_first(option):
    return (0 if option['id'] == CORE_TAG else 1, option['name'])


@handle_bad_request
def all_measures(request):
    tag_filter = _get_measure_tag_filter(request.GET, show_all_by_default=True)
    query = {}
    if tag_filter['tags']:
        query['tags__overlap'] = tag_filter['tags']
    measures = Measure.objects.filter(**query).order_by('name')
    context = {
        'tag_filter': tag_filter,
        'measures': measures
    }
    return render(request, 'all_measures.html', context)


def measure_for_all_ccgs(request, measure):
    measure = get_object_or_404(Measure, id=measure)
    context = {
        'measure': measure
    }
    return render(request, 'measure_for_all_ccgs.html', context)


def measure_for_practices_in_ccg(request, ccg_code, measure):
    requested_ccg = get_object_or_404(PCT, code=ccg_code)
    measure = get_object_or_404(Measure, id=measure)
    practices = Practice.objects.filter(ccg=requested_ccg)\
        .filter(setting=4).order_by('name')
    context = {
        'ccg': requested_ccg,
        'practices': practices,
        'page_id': ccg_code,
        'measure': measure
    }
    return render(request, 'measure_for_practices_in_ccg.html', context)


def _alerts_form(request, entity, entity_type):
    """Build a form for newsletter/alert signups, and handle user login
    for POSTs to that form.

    Because logins involve redirects, instead of returning a form, we
    sometimes return a redirect, which has to be handled differently
    in the calling code.

    Returns a triple of (form, already_signed_up, should_redirect)

    """
    assert entity_type in ['pct', 'practice']
    if request.method == 'POST':
        form = _handleCreateBookmark(
            request,
            OrgBookmark,
            OrgBookmarkForm,
            entity_type)
        if isinstance(form, HttpResponseRedirect):
            return (form, None, True)
    else:
        form = OrgBookmarkForm(
            initial={entity_type: entity.pk,
                     'email': getattr(request.user, 'email', '')})
    if request.user.is_authenticated():
        query = {entity_type: entity}
        signed_up_for_alert = request.user.orgbookmark_set.filter(
            **query)
    else:
        signed_up_for_alert = False
    return (form, signed_up_for_alert, None)


def ccg_home_page(request, ccg_code):
    ccg = get_object_or_404(PCT, code=ccg_code)
    # find the core measurevalue that is most outlierish
    extreme_measurevalue = MeasureValue.objects.filter(
        pct=ccg,
        practice__isnull=True,
        measure__tags__contains=['core']).order_by(
            '-percentile').first()
    if extreme_measurevalue:
        extreme_measure = extreme_measurevalue.measure
    else:
        extreme_measure = None
    request.session['came_from'] = request.path
    form, signed_up_for_alert, should_redirect = _alerts_form(
        request, ccg, 'pct')
    if should_redirect:
        return form
    practices = Practice.objects.filter(
        ccg=ccg).filter(setting=4).order_by('name')
    date = _specified_or_last_date(request, 'ppu')
    total_possible_savings = PPUSaving.objects.filter(
        date=date,
        pct=ccg,
        practice__isnull=True).aggregate(
            Sum('possible_savings'))['possible_savings__sum']
    measures_count = Measure.objects.count()
    context = {
        'measure': extreme_measure,
        'measures_count': measures_count,
        'entity': ccg,
        'entity_type': 'CCG',
        'entity_price_per_unit_url': 'ccg_price_per_unit',
        'measures_for_one_entity_url': 'measures_for_one_ccg',
        'possible_savings': total_possible_savings,
        'practices': practices,
        'date': date,
        'form': form,
        'signed_up_for_alert': signed_up_for_alert,
    }
    return render(request, 'entity_home_page.html', context)


def practice_home_page(request, practice_code):
    practice = get_object_or_404(Practice, code=practice_code)
    # find the core measurevalue that is most outlierish
    extreme_measurevalue = MeasureValue.objects.filter(
        practice=practice,
        measure__tags__contains=['core']).order_by(
            '-percentile').first()
    if extreme_measurevalue:
        extreme_measure = extreme_measurevalue.measure
    else:
        extreme_measure = None
    request.session['came_from'] = request.path
    form, signed_up_for_alert, should_redirect = _alerts_form(
        request, practice, 'practice')
    if should_redirect:
        return form
    date = _specified_or_last_date(request, 'ppu')
    total_possible_savings = PPUSaving.objects.filter(
        date=date,
        practice=practice).aggregate(
            Sum('possible_savings'))['possible_savings__sum']
    measures_count = Measure.objects.count()
    context = {
        'measure': extreme_measure,
        'measures_count': measures_count,
        'entity': practice,
        'entity_type': 'practice',
        'entity_price_per_unit_url': 'practice_price_per_unit',
        'measures_for_one_entity_url': 'measures_for_one_practice',
        'possible_savings': total_possible_savings,
        'date': date,
        'form': form,
        'signed_up_for_alert': signed_up_for_alert,
    }
    return render(request, 'entity_home_page.html', context)


@handle_bad_request
def measures_for_one_ccg(request, ccg_code):
    requested_ccg = get_object_or_404(PCT, code=ccg_code)
    tag_filter = _get_measure_tag_filter(request.GET)
    practices = Practice.objects.filter(
        ccg=requested_ccg).filter(
            setting=4).order_by('name')
    form, signed_up_for_alert, should_redirect = _alerts_form(
        request, requested_ccg, 'pct')
    if should_redirect:
        return form
    context = {
        'ccg': requested_ccg,
        'practices': practices,
        'page_id': ccg_code,
        'form': form,
        'signed_up_for_alert': signed_up_for_alert,
        'tag_filter': tag_filter
    }
    return render(request, 'measures_for_one_ccg.html', context)


def measure_for_one_ccg(request, measure, ccg_code):
    ccg = get_object_or_404(PCT, code=ccg_code)
    measure = get_object_or_404(Measure, pk=measure)
    context = {
        'ccg': ccg,
        'measure': measure,
        'current_at': ImportLog.objects.latest_in_category(
            'prescribing').current_at
    }
    return render(request, 'measure_for_one_ccg.html', context)


def measure_for_one_practice(request, measure, practice_code):
    practice = get_object_or_404(Practice, code=practice_code)
    measure = get_object_or_404(Measure, pk=measure)
    context = {
        'practice': practice,
        'measure': measure,
        'current_at': ImportLog.objects.latest_in_category(
            'prescribing').current_at
    }
    return render(request, 'measure_for_one_practice.html', context)


def finalise_signup(request):
    """Redirect the logged in user to the CCG they last bookmarked, or if
    they're not logged in, just go straight to the homepage -- both
    with a message.

    If there is a newsletter_email key, first redirect them to a page
    where we can capture more metadata about the user.

    """
    if 'newsletter_email' in request.POST:
        # Prompt the user for their metadata
        return render(request, 'newsletter_signup.html')
    else:
        next_url = None
        if request.method == 'POST':
            if 'newsletter_email' in request.session:
                # They've signed up to the newsletter
                mailchimp_subscribe(
                    request,
                    request.POST['email'], request.POST['first_name'],
                    request.POST['last_name'], request.POST['organisation'],
                    request.POST['job_title']
                )
                messages.success(
                    request,
                    'You have successfully signed up for the newsletter.')
        if 'alerts_requested' in request.session:
            # Their first alert bookmark signup
            del(request.session['alerts_requested'])
            messages.success(
                request, "Thanks, you're now subscribed to monthly alerts.")
        if request.user.is_authenticated():
            # The user is signing up to at least the second bookmark
            # in this session.
            try:
                last_bookmark = request.user.profile.most_recent_bookmark()
                next_url = last_bookmark.dashboard_url()
                messages.success(
                    request,
                    mark_safe("You're now subscribed to monthly "
                              "alerts about <em>%s</em>." %
                              last_bookmark.topic()))
            except AttributeError:
                # We've reached a strange place where they activated
                # an account but didn't subcribe. I'm not sure if/how
                # we would ever get to this bit?
                next_url = 'home'
                messages.success(
                    request,
                    "Your account is activated, but you are not subscribed "
                    "to any monthly alerts!")
            return redirect(next_url)
        else:
            if next_url:
                return redirect(next_url)
            else:
                return redirect(request.session.get('came_from', 'home'))


def analyse(request):
    if request.method == 'POST':
        form = _handleCreateBookmark(
            request,
            SearchBookmark,
            SearchBookmarkForm,
            'url', 'name'
        )
        if isinstance(form, HttpResponseRedirect):
            return form
    else:
        # Note that the (hidden) URL field is filled via javascript on
        # page load (see `alertForm` in `chart.js`)
        form = SearchBookmarkForm(
            initial={'email': getattr(request.user, 'email', '')})
    alert_preview_action = reverse('preview-analyse-bookmark')
    context = {
        'alert_preview_action': alert_preview_action,
        'form': form
    }
    return render(request, 'analyse.html', context)


def mailchimp_subscribe(
        request, email, first_name, last_name,
        organisation, job_title):
    del(request.session['newsletter_email'])
    email_hash = hashlib.md5(email).hexdigest()
    data = {
        'email_address': email,
        'status': 'subscribed',
        'merge_fields': {
            'FNAME': first_name,
            'LNAME': last_name,
            'MMERGE3': organisation,
            'MMERGE4': job_title
        }
    }
    client = MailChimp(
        get_env_setting('MAILCHIMP_USER'),
        get_env_setting('MAILCHIMP_API_KEY'))
    try:
        client.lists.members.get(
            list_id=settings.MAILCHIMP_LIST_ID,
            subscriber_hash=email_hash)
    except HTTPError:
        try:
            client.lists.members.create(
                list_id=settings.MAILCHIMP_LIST_ID, data=data)
        except HTTPError:
            # things like blacklisted emails, etc
            pass


def _handleCreateBookmark(request, subject_class,
                          subject_form_class,
                          *subject_field_ids):
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
            try:
                user = User.objects.create_user(
                    username=email, email=email)
            except IntegrityError:
                user = User.objects.get(username=email)
            user = authenticate(key=user.profile.key)
            kwargs = {
                'user': user
            }
            for field in subject_field_ids:
                kwargs[field] = form.cleaned_data[field]
            # An unverified account can only create unapproved bookmarks.
            # When an account is verified, all its bookmarks are
            # approved. Whenever someone tries to add a bookmark for
            # someone else's email address (or they're not logged in),
            # that email address is marked as unverified again.  In this
            # way we can allow people who remain logged in to add several
            # alerts without having to reconfirm by email.
            emailaddress = EmailAddress.objects.filter(user=user)
            if user == request.user:
                kwargs['approved'] = emailaddress.filter(
                    verified=True).exists()
            else:
                kwargs['approved'] = False
                emailaddress.update(verified=False)
            subject_class.objects.get_or_create(**kwargs)
            if hasattr(request, 'user'):
                # Log the user out. We don't use Django's built-in logout
                # mechanism because that clears the entire session, too,
                # and we want to know if someone's logged in previously in
                # this session.
                request.user = AnonymousUser()
                for k in [SESSION_KEY, BACKEND_SESSION_KEY, HASH_SESSION_KEY]:
                    if k in request.session:
                        del(request.session[k])
            # Users that are not verified are redirected by
            # django-allauth to the template at
            # `templates/account/verification_sent.html` (and are sent
            # a verification email).  Users who are already verified
            # are redirected to LOGIN_REDIRECT_URL.
            return perform_login(
                request, user,
                app_settings.EmailVerificationMethod.MANDATORY,
                signup=True)
        else:
            return redirect('newsletter-signup')
    return form


@handle_bad_request
def measures_for_one_practice(request, code):
    p = get_object_or_404(Practice, code=code)
    tag_filter = _get_measure_tag_filter(request.GET)
    alert_preview_action = reverse('preview-practice-bookmark', args=[p.code])
    form, signed_up_for_alert, should_redirect = _alerts_form(
        request, p, 'practice')
    if should_redirect:
        return form
    context = {
        'practice': p,
        'alert_preview_action': alert_preview_action,
        'page_id': code,
        'form': form,
        'signed_up_for_alert': signed_up_for_alert,
        'tag_filter': tag_filter
    }
    return render(request, 'measures_for_one_practice.html', context)


def gdoc_view(request, doc_id):
    try:
        gdoc_id = settings.GDOC_DOCS[doc_id]
    except KeyError:
        raise Http404("No doc named %s" % doc_id)
    url = 'https://docs.google.com/document/d/%s/pub?embedded=true' % gdoc_id
    page = requests.get(url)
    tree = html.fromstring(page.text)

    content = '<style>' + ''.join(
        [html.tostring(child)
         for child in tree.head.xpath('//style')]) + '</style>'
    content += ''.join(
        [html.tostring(child)
         for child in tree.body])
    context = {
        'content': content
    }
    return render(request, 'gdoc.html', context)


def tariff(request, code=None):
    products = DMDProduct.objects.filter(
        tariffprice__isnull=False,
        bnf_code__isnull=False
    ).distinct().order_by('name')
    codes = []
    if code:
        codes = [code]
    if 'codes' in request.GET:
        codes.extend(request.GET.getlist('codes'))
    if codes:
        presentations = Presentation.objects.filter(bnf_code__in=codes)
    else:
        presentations = []
    context = {
        'bnf_codes': codes,
        'presentations': presentations,
        'products': products,
        'chart_title': 'Tariff prices for ' + ', '.join(
            [x.product_name for x in presentations])
    }
    return render(request, 'tariff.html', context)


##################################################
# Custom HTTP errors
##################################################
def custom_500(request):
    type_, value, traceback = sys.exc_info()
    context = {}
    if 'canceling statement due to statement timeout' in value.message:
        context['reason'] = ("The database took too long to respond.  If you "
                             "were running an analysis with multiple codes, "
                             "try again with fewer.")
    if (request.META.get('HTTP_ACCEPT', '').find('application/json') > -1 or
       request.is_ajax()):
        return HttpResponse(context['reason'], status=500)
    else:
        return render(request, '500.html', context, status=500)
