import datetime
from lxml import html
import re
from urllib import urlencode
from urlparse import urlparse, urlunparse
import functools
import logging
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
from django.core.urlresolvers import get_resolver
from django.db import connection
from django.db.models import Avg, Sum
from django.http import Http404
from django.http import HttpResponse
from django.http.response import HttpResponseRedirect
from django.shortcuts import redirect
from django.shortcuts import render, get_object_or_404
from django.urls import reverse
from django.utils.http import is_safe_url
from django.utils.safestring import mark_safe

from allauth.account import app_settings
from allauth.account.models import EmailAddress
from allauth.account.utils import perform_login
from dateutil.relativedelta import relativedelta

from common.utils import parse_date
from api.view_utils import dictfetchall
from common.utils import ppu_sql
from dmd.models import DMDProduct
from frontend.forms import FeedbackForm
from frontend.forms import MonthlyOrgBookmarkForm
from frontend.forms import NonMonthlyOrgBookmarkForm
from frontend.forms import SearchBookmarkForm
from frontend.models import Chemical
from frontend.models import ImportLog
from frontend.models import Measure
from frontend.models import MeasureValue
from frontend.models import MeasureGlobal
from frontend.models import MEASURE_TAGS
from frontend.models import OrgBookmark
from frontend.models import NCSOConcessionBookmark
from frontend.models import Practice, PCT, Section
from frontend.models import Presentation
from frontend.models import RegionalTeam
from frontend.models import STP
from frontend.models import SearchBookmark
from frontend.feedback import send_feedback_mail
from frontend.views.spending_utils import (
    ncso_spending_for_entity, ncso_spending_breakdown_for_entity,
    NATIONAL_AVERAGE_DISCOUNT_PERCENTAGE
)
from frontend.views.mailchimp_utils import mailchimp_subscribe

logger = logging.getLogger(__name__)


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


def _first_or_none(lst):
    try:
        return lst[0]
    except IndexError:
        return None


##################################################
# BNF sections
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
# Chemicals
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
# GP practices
##################################################

def all_practices(request):
    practices = Practice.objects.filter(setting=4).order_by('name')
    context = {
        'practices': practices
    }
    return render(request, 'all_practices.html', context)


def practice_home_page(request, practice_code):
    practice = get_object_or_404(Practice, code=practice_code)
    form = _monthly_bookmark_and_newsletter_form(
        request, practice)
    if isinstance(form, HttpResponseRedirect):
        return form
    context = _home_page_context_for_entity(request, practice)
    context['form'] = form
    request.session['came_from'] = request.path
    return render(request, 'entity_home_page.html', context)


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


def ccg_home_page(request, ccg_code):
    ccg = get_object_or_404(PCT, code=ccg_code)
    form = _monthly_bookmark_and_newsletter_form(
        request, ccg)
    if isinstance(form, HttpResponseRedirect):
        return form
    practices = Practice.objects.filter(ccg=ccg, setting=4).order_by('name')
    context = _home_page_context_for_entity(request, ccg)
    context['form'] = form
    context['practices'] = practices
    request.session['came_from'] = request.path
    return render(request, 'entity_home_page.html', context)


##################################################
# STPs
##################################################

def all_stps(request):
    stps = STP.objects.order_by('name')
    context = {
        'stps': stps
    }
    return render(request, 'all_stps.html', context)


def stp_home_page(request, stp_code):
    stp = get_object_or_404(STP, ons_code=stp_code)
    ccgs = PCT.objects.filter(
        stp=stp,
        close_date__isnull=True,
        org_type='CCG'
    ).order_by('name')
    context = _home_page_context_for_entity(request, stp)
    context['ccgs'] = ccgs
    request.session['came_from'] = request.path
    return render(request, 'entity_home_page.html', context)


##################################################
# Regional teams
##################################################

def all_regional_teams(request):
    regional_teams = RegionalTeam.objects.filter(close_date__isnull=True).order_by('name')
    context = {
        'regional_teams': regional_teams
    }
    return render(request, 'all_regional_teams.html', context)


def regional_team_home_page(request, regional_team_code):
    regional_team = get_object_or_404(RegionalTeam, code=regional_team_code)
    ccgs = PCT.objects.filter(
        regional_team=regional_team,
        close_date__isnull=True,
        org_type='CCG'
    ).order_by('name')
    context = _home_page_context_for_entity(request, regional_team)
    context['ccgs'] = ccgs
    request.session['came_from'] = request.path
    return render(request, 'entity_home_page.html', context)


##################################################
# All England
##################################################

@handle_bad_request
def all_england(request):
    tag_filter = _get_measure_tag_filter(request.GET)
    entity_type = request.GET.get('entity_type', 'CCG')
    date = _specified_or_last_date(request, 'ppu')
    ppu_savings = _all_england_ppu_savings(entity_type, date)
    measure_savings = _all_england_measure_savings(entity_type, date)
    low_priority_savings = _all_england_low_priority_savings(entity_type, date)
    low_priority_total = _all_england_low_priority_total(entity_type, date)
    ncso_spending = _first_or_none(
        ncso_spending_for_entity(None, 'all_england', num_months=1)
    )
    other_entity_type = 'practice' if entity_type == 'CCG' else 'CCG'
    other_entity_query = request.GET.copy()
    other_entity_query['entity_type'] = other_entity_type

    measure_options = {
       'tags': ','.join(tag_filter['tags']),
       'orgType': entity_type.lower(),
       'orgName': 'All {}s in England'.format(entity_type),
       'aggregate': True,
       'rollUpBy': 'measure_id',
    }
    measure_options = _build_measure_options(measure_options)

    context = {
        'tag_filter': tag_filter,
        'entity_type': entity_type,
        'other_entity_type': other_entity_type,
        'other_entity_url': '?' + other_entity_query.urlencode(),
        'ppu_savings': ppu_savings,
        'measure_savings': measure_savings,
        'low_priority_savings': low_priority_savings,
        'low_priority_total': low_priority_total,
        'ncso_spending': ncso_spending,
        'date': date,
        'measure_options': measure_options,
    }
    return render(request, 'all_england.html', context)


##################################################
# Analyse
##################################################

def analyse(request):
    if request.method == 'POST':
        # should this be the _bookmark_and_newsletter_form?
        form = _handle_bookmark_and_newsletter_post(
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
    return render(request, 'analyse.html', {'form': form})


##################################################
# Measures
##################################################

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


def measure_for_one_entity(request, measure, entity_code, entity_type):
    entity = _get_entity(entity_type, entity_code)
    measure = get_object_or_404(Measure, pk=measure)

    measure_options = {
        'rollUpBy': 'measure_id',
        'measure': measure,
        'orgId': entity.code,
        'orgName': entity.name,
        'orgType': _org_type_for_entity(entity),
    }

    if isinstance(entity, Practice):
        measure_options['parentOrgId'] = entity.ccg_id

    measure_options = _build_measure_options(measure_options)

    entity_type_human = _entity_type_human(entity_type)
    context = {
        'entity': entity,
        'entity_type': entity_type,
        'entity_type_human': entity_type_human,
        'measures_url_name': 'measures_for_one_{}'.format(entity_type),
        'measure': measure,
        'measure_options': measure_options,
        'current_at': ImportLog.objects.latest_in_category(
            'prescribing').current_at
    }
    return render(request, 'measure_for_one_entity.html', context)


# Note that we cannot have a single view function for measures_for_one_entity or
# measure_for_children_in_entity (as we do for eg measure_for_one_entity)
# because the parameter names are used for building URLs by _url_template()
# below and _buildUrl() in measure_utils.js.

@handle_bad_request
def measures_for_one_practice(request, practice_code):
    return _measures_for_one_entity(request, practice_code, 'practice')


@handle_bad_request
def measures_for_one_ccg(request, ccg_code):
    return _measures_for_one_entity(request, ccg_code, 'ccg')


@handle_bad_request
def measures_for_one_stp(request, stp_code):
    return _measures_for_one_entity(request, stp_code, 'stp')


@handle_bad_request
def measures_for_one_regional_team(request, regional_team_code):
    return _measures_for_one_entity(request, regional_team_code, 'regional_team')


def _measures_for_one_entity(request, entity_code, entity_type):
    entity = _get_entity(entity_type, entity_code)
    tag_filter = _get_measure_tag_filter(request.GET)

    measure_options = {
        'rollUpBy': 'measure_id',
        'tags': ','.join(tag_filter['tags']),
        'orgId': entity.code,
        'orgName': entity.name,
        'orgType': _org_type_for_entity(entity),
    }

    if isinstance(entity, Practice):
        measure_options['parentOrgId'] = entity.ccg_id

    measure_options = _build_measure_options(measure_options)

    context = {
        'entity': entity,
        'entity_type': entity_type,
        'entity_type_human': _entity_type_human(entity_type),
        'page_id': entity_code,
        'tag_filter': tag_filter,
        'measure_options': measure_options,
    }

    if entity_type == 'ccg':
        context['practices'] = entity.practice_set.filter(setting=4).order_by('name')
    elif entity_type in ['stp', 'regional_team']:
        context['ccgs'] = entity.pct_set.filter(
            close_date__isnull=True,
            org_type='CCG'
        ).order_by('name')

    return render(request, 'measures_for_one_entity.html', context)


def measure_for_practices_in_ccg(request, ccg_code, measure):
    return _measure_for_children_in_entity(request, measure, ccg_code, 'ccg')


def measure_for_ccgs_in_stp(request, stp_code, measure):
    return _measure_for_children_in_entity(request, measure, stp_code, 'stp')


def measure_for_ccgs_in_regional_team(request, regional_team_code, measure):
    return _measure_for_children_in_entity(
        request,
        measure,
        regional_team_code,
        'regional_team'
    )


def _measure_for_children_in_entity(
        request, measure, parent_entity_code, parent_entity_type
    ):

    parent = _get_entity(parent_entity_type, parent_entity_code)
    child_entity_type = {
        'ccg': 'practice',
        'stp': 'ccg',
        'regional_team': 'ccg',
    }[parent_entity_type]
    measure = get_object_or_404(Measure, pk=measure)

    measure_options = {
        'rollUpBy': 'org_id',
        'measure': measure,
        'orgType': child_entity_type,
        'orgId': parent.code,
        'orgName': parent.name,
        'parentOrgType': _org_type_for_entity(parent),
    }

    if measure.tags_focus:
        measure_options['tagsFocus'] = ','.join(measure.tags_focus)

    measure_options =  _build_measure_options(measure_options)

    context = {
        'parent_entity_type': parent_entity_type,
        'parent_entity_type_human': _entity_type_human(parent_entity_type),
        'child_entity_type_human': _entity_type_human(child_entity_type),
        'parent': parent,
        'page_id': parent_entity_code,
        'measure': measure,
        'measure_options': measure_options,
    }
    return render(request, 'measure_for_children_in_entity.html', context)


def measure_for_all_entities(request, measure, entity_type):
    measure = get_object_or_404(Measure, id=measure)

    measure_options = {
        'rollUpBy': 'org_id',
        'measure': measure,
        'orgType': entity_type,
    }

    if measure.tags_focus:
        measure_options['tagsFocus'] = ','.join(measure.tags_focus)

    measure_options = _build_measure_options(measure_options)

    entity_type_human = _entity_type_human(entity_type)

    context = {
        'measure': measure,
        'measure_options': measure_options,
        'entity_type': entity_type,
        'entity_type_human': entity_type_human,
    }
    return render(request, 'measure_for_all_entities.html', context)


##################################################
# Price per unit
##################################################

@handle_bad_request
def practice_price_per_unit(request, code):
    date = _specified_or_last_date(request, 'ppu')
    practice = get_object_or_404(Practice, code=code)
    context = {
        'entity': practice,
        'entity_name': practice.cased_name,
        'highlight': practice.code,
        'highlight_name': practice.cased_name,
        'date': date,
        'by_practice': True
    }
    return render(request, 'price_per_unit.html', context)


@handle_bad_request
def ccg_price_per_unit(request, code):
    date = _specified_or_last_date(request, 'ppu')
    ccg = get_object_or_404(PCT, code=code)
    context = {
        'entity': ccg,
        'entity_name': ccg.cased_name,
        'highlight': ccg.code,
        'highlight_name': ccg.cased_name,
        'date': date,
        'by_ccg': True
    }
    return render(request, 'price_per_unit.html', context)


@handle_bad_request
def all_england_price_per_unit(request):
    date = _specified_or_last_date(request, 'ppu')
    context = {
        'entity_name': 'NHS England',
        'highlight_name': 'NHS England',
        'date': date,
        'by_ccg': True,
        'entity_type': 'CCG',
        'aggregate': True
    }
    return render(request, 'price_per_unit.html', context)


@handle_bad_request
def price_per_unit_by_presentation(request, entity_code, bnf_code):
    date = _specified_or_last_date(request, 'ppu')
    presentation = get_object_or_404(Presentation, pk=bnf_code)
    product = presentation.dmd_product
    if len(entity_code) == 3:
        entity = get_object_or_404(PCT, code=entity_code)
    elif len(entity_code) == 6:
        entity = get_object_or_404(Practice, code=entity_code)

    params = {
        'format': 'json',
        'bnf_code': presentation.bnf_code,
        'highlight': entity.code,
        'date': date.strftime('%Y-%m-%d'),
    }

    if 'trim' in request.GET:
        params['trim'] = request.GET['trim']

    bubble_data_url = _build_api_url('bubble', params)

    context = {
        'entity': entity,
        'entity_name': entity.cased_name,
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


@handle_bad_request
def all_england_price_per_unit_by_presentation(request, bnf_code):
    date = _specified_or_last_date(request, 'ppu')
    presentation = get_object_or_404(Presentation, pk=bnf_code)
    product = presentation.dmd_product

    params = {
        'format': 'json',
        'bnf_code': presentation.bnf_code,
        'date': date.strftime('%Y-%m-%d'),
    }

    if 'trim' in request.GET:
        params['trim'] = request.GET['trim']

    bubble_data_url = _build_api_url('bubble', params)

    context = {
        'name': presentation.product_name,
        'bnf_code': presentation.bnf_code,
        'presentation': presentation,
        'product': product,
        'date': date,
        'by_presentation': True,
        'bubble_data_url': bubble_data_url,
        'entity_name': 'NHS England',
        'entity_type': 'CCG',
    }
    return render(request, 'price_per_unit.html', context)


##################################################
# Ghost generics
##################################################

@handle_bad_request
def ghost_generics_for_entity(request, code, entity_type):
    date = _specified_or_last_date(request, 'prescribing')
    entity = _get_entity(entity_type, code)
    measure_for_entity_url = reverse(
        'measure_for_one_{}'.format(entity_type.lower()),
        kwargs={'measure': 'ghost_generic_measure', 'entity_code': code}
    )
    context = {
        'entity': entity,
        'entity_name': entity.cased_name,
        'entity_type': entity_type,
        'highlight': entity.code,
        'highlight_name': entity.cased_name,
        'date': date,
        'measure_for_entity_url': measure_for_entity_url,
    }
    if entity_type == 'practice':
        context['by_practice'] = True
    elif entity_type == 'CCG':
        context['by_ccg'] = True
    else:
        raise ValueError('Unhandled entity_type: {}'.format(entity_type))
    return render(request, 'ghost_generics.html', context)


##################################################
# Tariffs
##################################################

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
# Bookmarks
##################################################

def finalise_signup(request):
    """Handle mailchimp signups.

    Then redirect the logged in user to the CCG they last bookmarked, or if
    they're not logged in, just go straight to the homepage -- both
    with a message.

    This method should be configured as the LOGIN_REDIRECT_URL,
    i.e. the view that is called following any successful login, which
    in our case is always performed by _handle_bookmark_and_newsletter_post.

    """
    # Users who are logged in are *REDIRECTED* here, which means the
    # form is never shown.
    next_url = None
    if 'newsletter_email' in request.session:
        if request.POST:
            success = mailchimp_subscribe(
                request,
                request.POST['email'], request.POST['first_name'],
                request.POST['last_name'], request.POST['organisation'],
                request.POST['job_title']
            )
            if success:
                messages.success(
                    request,
                    'You have successfully signed up for the newsletter.')
            else:
                messages.error(
                    request,
                    'There was a problem signing you up for the newsletter.')

        else:
            # Show the signup form
            return render(request, 'newsletter_signup.html')
    if not request.user.is_authenticated():
        if 'alerts_requested' in request.session:
            # Their first alert bookmark signup
            del(request.session['alerts_requested'])
            messages.success(
                request, "Thanks, you're now subscribed to alerts.")
        if next_url:
            return redirect(next_url)
        else:
            return redirect(request.session.get('came_from', 'home'))
    else:
        # The user is signing up to at least the second bookmark
        # in this session.
        last_bookmark = request.user.profile.most_recent_bookmark()
        next_url = last_bookmark.dashboard_url()
        messages.success(
            request,
            mark_safe("You're now subscribed to alerts about <em>%s</em>." %
                      last_bookmark.topic()))
        return redirect(next_url)


##################################################
# Spending
##################################################

def spending_for_one_entity(request, entity_code, entity_type):
    # Temporary hack as this page is very expensive to render and brings the
    # site to its knees when bots decide to crawl us (most other pages do the
    # expensive data loading via JS and so don't have this issue)
    if _user_is_bot(request):
        raise Http404()

    entity = _get_entity(entity_type, entity_code)

    form = _ncso_concession_bookmark_and_newsletter_form(request, entity)
    if isinstance(form, HttpResponseRedirect):
        return form

    monthly_totals = ncso_spending_for_entity(
        entity, entity_type,
        num_months=12,
        current_month=_get_current_month()
    )
    # In the very rare cases where we don't have data we just return a 404
    # rather than triggering an error
    if not monthly_totals:
        raise Http404('No data available')
    end_date = max(row['month'] for row in monthly_totals)
    last_prescribing_date = monthly_totals[-1]['last_prescribing_date']
    rolling_annual_total = sum(row['additional_cost'] for row in monthly_totals)
    financial_ytd_total = _financial_ytd_total(monthly_totals)
    breakdown_date = request.GET.get('breakdown_date')
    breakdown_date = parse_date(breakdown_date).date() if breakdown_date else end_date
    breakdown = ncso_spending_breakdown_for_entity(entity, entity_type, breakdown_date)
    breakdown_metadata = [i for i in monthly_totals if i['month'] == breakdown_date][0]
    url_template = (
        reverse('tariff', kwargs={'code': 'AAA'})
        .replace('AAA', '{bnf_code}')
    )
    if entity_type == 'all_england':
        entity_name = 'NHS England'
        title = 'Impact of price concessions across {}'.format(entity_name)
        entity_short_desc = 'nhs-england'
    else:
        entity_name = entity.cased_name
        title = 'Impact of price concessions on {}'.format(entity_name)
        entity_short_desc = '{}-{}'.format(entity_type, entity.code)
    context = {
        'title': title,
        'entity_name': entity_name,
        'monthly_totals': monthly_totals,
        'rolling_annual_total': rolling_annual_total,
        'financial_ytd_total': financial_ytd_total,
        'available_dates': [row['month'] for row in reversed(monthly_totals)],
        'breakdown': {
            'table': breakdown,
            'url_template': url_template,
            'filename': 'price-concessions-cost-{}-{}'.format(
                entity_short_desc,
                breakdown_date
            )
        },
        'breakdown_date': breakdown_date,
        'breakdown_is_estimate': breakdown_metadata['is_estimate'],
        'breakdown_is_incomplete_month': breakdown_metadata['is_incomplete_month'],
        'last_prescribing_date': last_prescribing_date,
        'national_average_discount_percentage': NATIONAL_AVERAGE_DISCOUNT_PERCENTAGE,
        'signed_up_for_alert': _signed_up_for_alert(request, entity, NCSOConcessionBookmark),
        'form': form,
    }
    request.session['came_from'] = request.path
    return render(request, 'spending_for_one_entity.html', context)


def _user_is_bot(request):
    user_agent = request.META.get('HTTP_USER_AGENT', '')
    # Despite appearances this is actually a fairly robust way of detecting bots
    # See: https://webmasters.stackexchange.com/a/64805
    match = re.search('(bot|crawl|spider)', user_agent.lower())
    return bool(match)


def _get_current_month():
    return datetime.datetime.now().date().replace(day=1)


def _financial_ytd_total(monthly_totals):
    end_date = max(row['month'] for row in monthly_totals)
    financial_year = end_date.year if end_date.month >= 4 else end_date.year - 1
    financial_year_start = end_date.replace(year=financial_year, month=4)
    return sum(
        row['additional_cost'] for row in monthly_totals
        if row['month'] >= financial_year_start
    )


##################################################
# Misc.
##################################################

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


def feedback_view(request):
    url = request.GET.get('from_url', '/')
    if request.POST:
        form = FeedbackForm(request.POST)
        if form.is_valid():
            user_name = form.cleaned_data['name'].strip()
            user_email_addr = form.cleaned_data['email'].strip()
            send_feedback_mail(
                user_name=user_name,
                user_email_addr=user_email_addr,
                subject=form.cleaned_data['subject'].strip(),
                message=form.cleaned_data['message'],
                url=url,
            )

            msg = ("Thanks for sending your feedback/query! A copy of the "
                   "message has been sent to you at {}. Please check your spam "
                   "folder for our reply.".format(user_email_addr))
            messages.success(request, msg)

            if is_safe_url(url, allowed_hosts=[request.get_host()]):
                redirect_url = url
            else:
                logger.error(u'Unsafe redirect URL: {}'.format(url))
                redirect_url = '/'
            return HttpResponseRedirect(redirect_url)
    else:
        form = FeedbackForm()

    show_warning = '/practice/' in url

    return render(request, 'feedback.html', {
        'form': form,
        'show_warning': show_warning
    })


##################################################
# Custom HTTP errors
##################################################
def custom_500(request):
    type_, value, traceback = sys.exc_info()
    reason = 'Server error'
    if 'canceling statement due to statement timeout' in unicode(value):
        reason = (
            "The database took too long to respond.  If you were running an"
            "analysis with multiple codes, try again with fewer."
        )
    if request.is_ajax() or 'application/json' in request.META.get('HTTP_ACCEPT', ''):
        return HttpResponse(reason, status=500)
    else:
        return render(request, '500.html', {'reason': reason}, status=500)


# This view deliberately triggers an error
def error(request):
    raise RuntimeError('Deliberate error triggered for testing purposes')


##################################################
# Helpers
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


def _total_savings(entity, date):
    conditions = ' '
    if isinstance(entity, PCT):
        conditions += 'AND {ppusavings_table}.pct_id = %(entity_code)s '
        conditions += 'AND {ppusavings_table}.practice_id IS NULL '
    elif isinstance(entity, Practice):
        conditions += 'AND {ppusavings_table}.practice_id = %(entity_code)s '
    sql = ppu_sql(conditions=conditions)
    sql = ("SELECT SUM(possible_savings) "
           "AS total_savings FROM ({}) all_savings").format(sql)
    params = {'date': date, 'entity_code': entity.pk}
    with connection.cursor() as cursor:
        cursor.execute(sql, params)
        return dictfetchall(cursor)[0]['total_savings']


def _home_page_context_for_entity(request, entity):
    prescribing_date = ImportLog.objects.latest_in_category(
        'prescribing').current_at
    six_months_ago = prescribing_date - relativedelta(months=6)
    mv_filter = {
        'month__gte': six_months_ago,
        'measure__tags__contains': ['core'],
        'percentile__isnull': False
    }
    if isinstance(entity, Practice):
        mv_filter['practice_id'] = entity.code
        entity_type = 'practice'
        parent_org = entity.ccg_id
    elif isinstance(entity, PCT):
        mv_filter['pct_id'] = entity.code
        mv_filter['practice_id'] = None
        entity_type = 'ccg'
        parent_org = None
    elif isinstance(entity, STP):
        mv_filter['stp_id'] = entity.code
        mv_filter['pct_id'] = None
        mv_filter['practice_id'] = None
        entity_type = 'stp'
        parent_org = None
    elif isinstance(entity, RegionalTeam):
        mv_filter['regional_team_id'] = entity.code
        mv_filter['pct_id'] = None
        mv_filter['practice_id'] = None
        entity_type = 'regional_team'
        parent_org = None
    else:
        raise RuntimeError("Can't handle type: {!r}".format(entity))
    # find the core measurevalue that is most outlierish
    extreme_measurevalue = (
        MeasureValue.objects
        .filter(**mv_filter)
        .exclude(measure_id='lpzomnibus')
        .values('measure_id')
        .annotate(average_percentile=Avg('percentile'))
        .order_by('-average_percentile')
        .first()
    )
    if extreme_measurevalue:
        extreme_measure = Measure.objects.get(
            pk=extreme_measurevalue['measure_id'])
    else:
        extreme_measure = None
    ppu_date = _specified_or_last_date(request, 'ppu')
    total_possible_savings = _total_savings(entity, ppu_date)
    measures_count = Measure.objects.count()

    specific_measures = [{
          'measure': 'lpzomnibus',
          'chartContainerId': '#lpzomnibus-container',
    }]

    if extreme_measure:
        # extreme_measure will be None for new practices (and in tests)
        specific_measures.append({
          'measure': extreme_measure.id,
          'chartContainerId': '#top-measure-container',
        })

    measure_options = {
        'rollUpBy': 'measure_id',
        'specificMeasures': specific_measures,
        'orgId': entity.code,
        'orgType': _org_type_for_entity(entity),
    }

    if isinstance(entity, Practice):
        measure_options['parentOrgId'] = entity.ccg_id

    measure_options = _build_measure_options(measure_options)

    # This will blow up loudly if we remove this tag, at which point we should
    # also remove the corresponding link from the entity_home_page.html
    # template
    assert 'lowpriorityconsultation' in MEASURE_TAGS

    context = {
        'measure': extreme_measure,
        'measures_count': measures_count,
        'entity': entity,
        'entity_type': entity_type,
        'entity_type_human': _entity_type_human(entity_type),
        'measures_for_one_entity_url': 'measures_for_one_{}'.format(
            entity_type.lower().replace(' ', '_')),
        'possible_savings': total_possible_savings,
        'date': ppu_date,
        'measure_options': measure_options,
        'measure_tags': [
            (k, v) for (k, v) in sorted(MEASURE_TAGS.items())
            if k != 'core'
        ]
    }

    if entity_type in ['practice', 'ccg']:
        context['entity_price_per_unit_url'] = '{}_price_per_unit'.format(
            entity_type.lower())
        context['date'] = _specified_or_last_date(request, 'ppu')
        context['possible_savings'] = _total_savings(entity, context['date'])
        context['ncso_spending'] =  _first_or_none(
            ncso_spending_for_entity(entity, entity_type, num_months=1)
        )
        context['entity_ghost_generics_url'] = '{}_ghost_generics'.format(
            entity_type.lower())
        context['spending_for_one_entity_url'] = 'spending_for_one_{}'.format(
            entity_type.lower())
        context['signed_up_for_alert'] = _signed_up_for_alert(
            request, entity, OrgBookmark)

    return context


def _url_template(view_name):
    resolver = get_resolver()
    pattern = resolver.reverse_dict[view_name][1]
    pattern = '/' + pattern.rstrip('$')
    return re.sub('\(\?P<(\w+)>\[.*?]\+\)', '{\\1}', pattern)


def _org_type_for_entity(entity):
    return {
        Practice: 'practice',
        PCT: 'ccg',
        STP: 'stp',
        RegionalTeam: 'regional_team',
    }[type(entity)]


def _build_measure_options(options):
    # measure etc
    if 'measure' in options:
        measure = options['measure']
        options['measure'] = measure.id
        options['numerator'] = measure.numerator_short
        options['denominator'] = measure.denominator_short
        options['isCostBasedMeasure'] = measure.is_cost_based
        options['lowIsGood'] = measure.low_is_good

    # globalMeasuresUrl & panelMeasuresUrl
    params = {'format': 'json'}
    if 'measure' in options:
        params['measure'] = options['measure']
    if 'specificMeasures' in options:
        params['measure'] = ','.join(
            specific_measure['measure']
            for specific_measure in options['specificMeasures']
        )
    if 'tags' in options:
        params['tags'] = options['tags']

    options['globalMeasuresUrl'] = _build_api_url('measure', params)

    if 'orgId' in options:
        params['org'] = options['orgId']
    if 'aggregate' in options:
        params['aggregate'] = options['aggregate']
    if 'parentOrgType' in options:
        params['parent_org_type'] = options['parentOrgType'].lower().replace(' ', '_')

    view_name = 'measure_by_' + options['orgType']
    options['panelMeasuresUrl'] = _build_api_url(view_name, params)

    # orgLocationUrl
    if 'orgId' in options:
        org_location_params = {
            'org_type': options['orgType'],
            'q': options['orgId'],
        }

        options['orgLocationUrl'] = _build_api_url(
            'org_location',
            org_location_params
        )

    # chartTitleUrlTemplate
    if options['rollUpBy'] == 'measure_id':
        if options.get('aggregate'):
            options['chartTitleUrlTemplate'] = _url_template('measure_for_all_ccgs')
        elif options['orgType'] == 'regional_team':
            options['chartTitleUrlTemplate'] = _url_template('measure_for_ccgs_in_regional_team')
        elif options['orgType'] == 'stp':
            options['chartTitleUrlTemplate'] = _url_template('measure_for_ccgs_in_stp')
        else:
            options['chartTitleUrlTemplate'] = _url_template('measure_for_practices_in_ccg')
    else:
        view_name = 'measures_for_one_{}'.format(options['orgType'])
        options['chartTitleUrlTemplate'] = _url_template(view_name)

    # measureForAllPracticesUrlTemplate
    if not options.get('aggregate') and options['orgType'] == 'ccg':
        options['measureForAllPracticesUrlTemplate'] = _url_template('measure_for_practices_in_ccg')

    # measureForAllCCGsUrlTemplate
    if options['orgType'] in ['stp', 'regional_team']:
        view_name = 'measure_for_ccgs_in_{}'.format(options['orgType'])
        options['measureForAllCCGsUrlTemplate'] = _url_template(view_name)

    # measureUrlTemplate
    if options['rollUpBy'] == 'measure_id':
        if options['orgType'] == 'practice':
            view_name = 'measure_for_all_ccgs'
        else:
            view_name = 'measure_for_all_{}s'.format(options['orgType'])
        options['measureUrlTemplate'] = _url_template(view_name)

    # oneEntityUrlTemplate
    if not options.get('aggregate') and not (options['rollUpBy'] == 'measure_id' and 'measure' in options):
        # If we're rolling up by measure and a measure is provided in the
        # options, then we are already on the measure_for_one_xxx page, so we
        # shouldn't set oneEntityUrlTemplate.
        view_name = 'measure_for_one_{}'.format(options['orgType'])
        options['oneEntityUrlTemplate'] = _url_template(view_name)

    # tagsFocusUrlTemplate
    if options.get('aggregate'):
        options['tagsFocusUrlTemplate'] = reverse('all_england')
    else:
        view_name = 'measures_for_one_{}'.format(options['orgType'])
        options['tagsFocusUrlTemplate'] = _url_template(view_name)

    options['orgTypeHuman'] = _entity_type_human(options['orgType'])
    if 'parentOrgType' in options:
        options['parentOrgTypeHuman'] = _entity_type_human(options['parentOrgType'])

    return options


def _build_api_url(view_name, params):
    path = reverse(view_name)
    querystring = urlencode(params)

    parsed_url = urlparse(settings.API_HOST)

    return urlunparse((
        parsed_url.scheme, # scheme
        parsed_url.netloc, # host
        path,              # path
        '',                # params
        querystring,       # query
        '',                # fragment
    ))


def _all_england_ppu_savings(entity_type, date):
    conditions = ' '
    if entity_type == 'CCG':
        conditions += 'AND {ppusavings_table}.pct_id IS NOT NULL '
        conditions += 'AND {ppusavings_table}.practice_id IS NULL '
    elif entity_type == 'practice':
        conditions += 'AND {ppusavings_table}.practice_id IS NOT NULL '
    else:
        raise BadRequestError(u'Unknown entity type: {}'.format(entity_type))
    sql = ppu_sql(conditions=conditions)
    sql = ("SELECT SUM(possible_savings) "
           "AS total_savings FROM ({}) all_savings").format(sql)
    params = {'date': date}
    with connection.cursor() as cursor:
        cursor.execute(sql, params)
        savings = dictfetchall(cursor)[0]['total_savings']

    if savings is None:
        # This might happen when testing.
        return 0
    else:
        return savings


def _all_england_measure_savings(entity_type, date):
    return (
        MeasureValue.objects
        .filter(month=date, practice_id__isnull=(entity_type == 'CCG'))
        .exclude(measure_id='lpzomnibus')
        .aggregate_cost_savings()
    )


def _all_england_low_priority_savings(entity_type, date):
    target_costs = (
        MeasureGlobal.objects
        .get(month=date, measure_id='lpzomnibus')
        .percentiles[entity_type.lower()]
    )
    return (
        MeasureValue.objects.filter(
            month=date,
            measure_id='lpzomnibus',
            practice_id__isnull=(entity_type == 'CCG')
        )
        .calculate_cost_savings(target_costs)
    )


def _all_england_low_priority_total(entity_type, date):
    result = (
        MeasureValue.objects.filter(
            month=date,
            measure_id='lpzomnibus',
            practice_id__isnull=(entity_type == 'CCG')
        )
        .aggregate(total=Sum('numerator'))
    )
    return result['total']


def _authenticate_possibly_new_user(email):
    try:
        user = User.objects.get(username=email)
    except User.DoesNotExist:
        user = User.objects.create_user(
            username=email, email=email)
    return authenticate(key=user.profile.key)


def _unverify_email_address_when_different_user(user, request):
    # This is weird. Because entering any email address logs you in as that
    # user (see force_login function below) we need to prevent accessing
    # someone's bookmarks just by signing up using their email address. This is
    # done by unverifying that email address if you're not already logged in as
    # that user and then forcing a re-verification before you can access
    # existing bookmarks.
    emailaddress = EmailAddress.objects.filter(user=user)
    if user != request.user:
        emailaddress.update(verified=False)


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

    if not subject_field_ids:
        # There is no practice or PCT.
        form_args['practice'] = None
        form_args['pct'] = None

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


def _signed_up_for_alert(request, entity, subject_class):
    if request.user.is_authenticated():
        if entity:
            # Entity is a Practice or PCT
            q = {_entity_type_from_object(entity): entity}
        else:
            # Entity is "All England"
            q = {'practice_id__isnull': True, 'pct_id__isnull': True}
        return subject_class.objects.filter(user=request.user, **q).exists()
    else:
        return False


def _monthly_bookmark_and_newsletter_form(request, entity):
    """Build a form for newsletter/alert signups, and handle user login
    for POSTs to that form.
    """
    entity_type = _entity_type_from_object(entity)
    if request.method == 'POST':
        form = _handle_bookmark_and_newsletter_post(
            request,
            OrgBookmark,
            MonthlyOrgBookmarkForm,
            entity_type)
    else:
        form = MonthlyOrgBookmarkForm(
            initial={entity_type: entity.pk,
                     'email': getattr(request.user, 'email', '')})

    return form


def _ncso_concession_bookmark_and_newsletter_form(request, entity):
    """Build a form for newsletter/alert signups, and handle user login
    for POSTs to that form.
    """
    if entity is None:
        return _ncso_concession_bookmark_and_newsletter_form_for_all_england(request)

    entity_type = _entity_type_from_object(entity)
    if request.method == 'POST':
        form = _handle_bookmark_and_newsletter_post(
            request,
            NCSOConcessionBookmark,
            NonMonthlyOrgBookmarkForm,
            entity_type)
    else:
        form = NonMonthlyOrgBookmarkForm(
            initial={entity_type: entity.pk,
                     'email': getattr(request.user, 'email', '')})

    return form


def _ncso_concession_bookmark_and_newsletter_form_for_all_england(request):
    if request.method == 'POST':
        form = _handle_bookmark_and_newsletter_post(
            request,
            NCSOConcessionBookmark,
            NonMonthlyOrgBookmarkForm)
    else:
        form = NonMonthlyOrgBookmarkForm(
            initial={'email': getattr(request.user, 'email', '')})

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
            _unverify_email_address_when_different_user(user, request)
            # We're automatically approving all alert signups from now on
            # without waiting for the email address to be verified
            form_args['approved'] = True
            subject_class.objects.get_or_create(**form_args)
            return _force_login_and_redirect(request, user)
        else:
            return redirect('newsletter-signup')
    return form


def _get_entity(entity_type, entity_code):
    entity_type = entity_type.lower()

    if entity_type == 'practice':
        return get_object_or_404(Practice, code=entity_code)
    elif entity_type == 'ccg':
        return get_object_or_404(PCT, code=entity_code)
    elif entity_type == 'stp':
        return get_object_or_404(STP, ons_code=entity_code)
    elif entity_type == 'regional_team':
        return get_object_or_404(RegionalTeam, code=entity_code)
    elif entity_type == 'all_england':
        return None
    else:
        raise ValueError('Unknown entity_type: '+entity_type)


def _entity_type_human(entity_type):
    return {
        'practice': 'practice',
        'ccg': 'CCG',
        'stp': 'STP',
        'regional_team': 'Regional Team',
    }[entity_type]
