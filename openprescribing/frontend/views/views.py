import functools
from lxml import html
import requests
from urllib import urlencode
from urlparse import urlparse, urlunparse
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
from django.http import Http404
from django.http import HttpResponse
from django.http.response import HttpResponseRedirect
from django.shortcuts import redirect
from django.shortcuts import render, get_object_or_404
from django.utils.safestring import mark_safe

from allauth.account import app_settings
from allauth.account.models import EmailAddress
from allauth.account.utils import perform_login

from common.utils import parse_date
from dmd.models import DMDProduct
from frontend.forms import OrgBookmarkForm
from frontend.forms import SearchBookmarkForm
from frontend.models import Chemical
from frontend.models import ImportLog
from frontend.models import Measure, MEASURE_TAGS
from frontend.models import OrgBookmark
from frontend.models import Practice, PCT, Section
from frontend.models import Presentation
from frontend.models import SearchBookmark


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


def _get_measure_tag_filter(params, show_all_by_default=False):
    tags = params.get('tags', '').split(',')
    tags = filter(None, tags)
    default_tags = [] if show_all_by_default else ['core']
    if not tags:
        tags = default_tags
    try:
        tag_details = [MEASURE_TAGS[tag] for tag in tags]
    except KeyError as e:
        raise BadRequestError(u'Unrecognised tag: {}'.format(e.args[0]))
    name = ','.join([tag['name'] for tag in tag_details])
    descriptions = [tag.get('description') for tag in tag_details]
    description = mark_safe('<br><br>'.join(filter(None, descriptions)))
    return {
        'tags': tags,
        'name': name,
        'description': description,
        'show_message': (tags != default_tags)
    }


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


@handle_bad_request
def measures_for_one_ccg(request, ccg_code):
    requested_ccg = get_object_or_404(PCT, code=ccg_code.upper())
    tag_filter = _get_measure_tag_filter(request.GET)
    if request.method == 'POST':
        form = _handleCreateBookmark(
            request,
            OrgBookmark,
            OrgBookmarkForm,
            'pct')
        if isinstance(form, HttpResponseRedirect):
            return form
    else:
        form = OrgBookmarkForm(
            initial={'pct': requested_ccg.pk,
                     'email': getattr(request.user, 'email', '')})
    if request.user.is_authenticated():
        signed_up_for_alert = request.user.orgbookmark_set.filter(
            pct=requested_ccg)
    else:
        signed_up_for_alert = False
    practices = Practice.objects.filter(
        ccg=requested_ccg).filter(
            setting=4).order_by('name')
    alert_preview_action = reverse(
        'preview-ccg-bookmark', args=[requested_ccg.code])
    context = {
        'alert_preview_action': alert_preview_action,
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


def last_bookmark(request):
    """Redirect the logged in user to the CCG they last bookmarked, or if
    they're not logged in, just go straight to the homepage -- both
    with a message.

    """
    if request.user.is_authenticated():
        try:
            last_bookmark = request.user.profile.most_recent_bookmark()
            next_url = last_bookmark.dashboard_url()
            messages.success(
                request,
                mark_safe("Thanks, you're now subscribed to monthly "
                          "alerts about <em>%s</em>!" % last_bookmark.topic()))
        except AttributeError:
            next_url = 'home'
            messages.success(
                request,
                "Your account is activated, but you are not subscribed "
                "to any monthly alerts!")
        return redirect(next_url)
    else:
        messages.success(
            request, "Thanks, you're now subscribed to monthly alerts!")
        return redirect('home')


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


def _handleCreateBookmark(request, subject_class,
                          subject_form_class,
                          *subject_field_ids):
    form = subject_form_class(request.POST)
    if form.is_valid():
        email = form.cleaned_data['email']
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
            kwargs['approved'] = emailaddress.filter(verified=True).exists()
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
        return perform_login(
            request, user,
            app_settings.EmailVerificationMethod.MANDATORY,
            signup=True)
    return form


@handle_bad_request
def measures_for_one_practice(request, code):
    p = get_object_or_404(Practice, code=code)
    tag_filter = _get_measure_tag_filter(request.GET)
    if request.method == 'POST':
        form = _handleCreateBookmark(
            request,
            OrgBookmark,
            OrgBookmarkForm,
            'practice')
        if isinstance(form, HttpResponseRedirect):
            return form
    else:
        form = OrgBookmarkForm(
            initial={'practice': p.pk,
                     'email': getattr(request.user, 'email', '')})
    if request.user.is_authenticated():
        signed_up_for_alert = request.user.orgbookmark_set.filter(
            practice=p)
    else:
        signed_up_for_alert = False
    alert_preview_action = reverse('preview-practice-bookmark', args=[p.code])
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
