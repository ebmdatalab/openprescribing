import functools

from django.conf.urls import include, url
from django.urls import reverse
from django.views.generic import RedirectView, TemplateView
from django.contrib import admin
from django.http.response import HttpResponseRedirect
from frontend.views import views as frontend_views
from frontend.views import bookmark_views

admin.autodiscover()

handler500 = frontend_views.custom_500


# Added 2018-11-15: maybe revist in a year to see if still required
def redirect_if_tags_query(view_fn):
    """
    Redirect CCG/practice homepage requests if they have a "tags" query
    parameter

    We need this because these homepages used to show all measures which could
    be filtered by tag, but that content has since moved to the
    measures_for_one_X pages. Internal links have been updated but there are
    links which we don't control.
    """
    @functools.wraps(view_fn)
    def wrapper(request, **kwargs):
        if not request.GET.get('tags'):
            return view_fn(request, **kwargs)
        if 'ccg_code' in kwargs:
            url = reverse('measures_for_one_ccg', kwargs=kwargs)
        else:
            url = reverse(
                'measures_for_one_practice',
                kwargs={'code': kwargs['practice_code']})
        url = '{}?{}'.format(url, request.GET.urlencode())
        return HttpResponseRedirect(url)
    return wrapper


urlpatterns = [
    # Static pages.
    url(r'^$', TemplateView.as_view(template_name='index.html'), name="home"),
    url(r'^api/$', TemplateView.as_view(template_name='api.html'), name="api"),
    url(r'^about/$', TemplateView.as_view(template_name='about.html'),
        name="about"),
    url(r'^faq/$', TemplateView.as_view(template_name='faq.html'),
        name="faq"),
    url(r'^long_term_trends/$', TemplateView.as_view(template_name='long_term_trends.html'),
        name="long_term_trends"),
    url(r'^price-per-unit-faq/$', TemplateView.as_view(
        template_name='price_per_unit_faq.html'),
        name="price_per_unit_faq"),
    url(r'^privacy/$', TemplateView.as_view(template_name='privacy.html'),
        name="privacy"),
    url(r'^contact/$', TemplateView.as_view(template_name='contact.html'),
        name="contact"),
    url(r'^feedback/$', frontend_views.feedback_view, name="feedback"),
    url(r'^how-to-use/$',
        TemplateView.as_view(template_name='how-to-use.html'),
        name="how-to-use"),
    url(r'^alert_example/$',
        TemplateView.as_view(template_name='alert_example.html'),
        name="alert_example"),

    url(r'^500/$', frontend_views.error, name='error'),

    ##################################################
    # User-facing pages.
    ##################################################

    # BNF sections
    url(r'^bnf/$', frontend_views.all_bnf, name='all_bnf'),
    url(r'^bnf/(?P<section_id>[\d]+)/$', frontend_views.bnf_section,
        name='bnf_section'),

    # Chemicals
    url(r'^chemical/$', frontend_views.all_chemicals,
        name='all_chemicals'),
    url(r'^chemical/(?P<bnf_code>[A-Z\d]+)/$', frontend_views.chemical,
        name='chemical'),

    # GP practices
    url(r'^practice/$', frontend_views.all_practices,
        name='all_practices'),
    url(r'^practice/(?P<practice_code>[A-Z\d]+)/$',
        redirect_if_tags_query(frontend_views.practice_home_page),
        name='practice_home_page'),

    # CCGs
    url(r'^ccg/$', frontend_views.all_ccgs, name='all_ccgs'),
    url(r'^ccg/(?P<ccg_code>[A-Z\d]+)/$',
        redirect_if_tags_query(frontend_views.ccg_home_page),
        name='ccg_home_page'),

    # All England
    url(r'^all-england/$',
        frontend_views.all_england,
        name='all_england'),

    # Analyse
    url(r'^analyse/$', frontend_views.analyse,
        name="analyse"),

    # Price per unit
    # This must come above measures, as the measure_for_practices_in_ccg
    # pattern would also match the ccg_price_per_unit pattern.
    url(r'^practice/(?P<code>[A-Z\d]+)/price_per_unit/$',
        frontend_views.practice_price_per_unit,
        name='practice_price_per_unit'),
    url(r'^ccg/(?P<code>[A-Z\d]+)/price_per_unit/$',
        frontend_views.ccg_price_per_unit,
        name='ccg_price_per_unit'),
    url(r'^all-england/price-per-unit/$',
        frontend_views.all_england_price_per_unit,
        name='all_england_price_per_unit'),

    url(r'^practice/(?P<entity_code>[A-Z\d]+)/'
        '(?P<bnf_code>[A-Z\d]+)/price_per_unit/$',
        frontend_views.price_per_unit_by_presentation,
        name='price_per_unit_by_presentation_practice'),
    url(r'^ccg/(?P<entity_code>[A-Z\d]+)/'
        '(?P<bnf_code>[A-Z\d]+)/price_per_unit/$',
        frontend_views.price_per_unit_by_presentation,
        name='price_per_unit_by_presentation'),
    url(r'^all-england/(?P<bnf_code>[A-Z\d]+)/price-per-unit/$',
        frontend_views.all_england_price_per_unit_by_presentation,
        name='all_england_price_per_unit_by_presentation'),

    # Spending
    # (This must go above Measures because of the measure_for_practices_in_ccg
    # pattern)
    url(r'^practice/(?P<entity_code>[A-Z\d]+)/concessions/$',
        frontend_views.spending_for_one_entity,
        name='spending_for_one_practice',
        kwargs={'entity_type': 'practice'}),
    url(r'^ccg/(?P<entity_code>[A-Z\d]+)/concessions/$',
        frontend_views.spending_for_one_entity,
        name='spending_for_one_ccg',
        kwargs={'entity_type': 'CCG'}),
    url(r'^all-england/concessions/$',
        frontend_views.spending_for_one_entity,
        name='spending_for_all_england',
        kwargs={'entity_type': 'all_england', 'entity_code': None}),

    # Measures
    url(r'^measure/$',
        frontend_views.all_measures,
        name='all_measures'),

    url(r'^measure/(?P<measure>[A-Za-z\d_]+)/$',
        frontend_views.measure_for_all_ccgs,
        name='measure_for_all_ccgs'),

    url(r'^measure/(?P<measure>[A-Za-z\d_]+)/'
        'practice/(?P<practice_code>[A-Z\d]+)/$',
        frontend_views.measure_for_one_practice,
        name='measure_for_one_practice'),
    url(r'^measure/(?P<measure>[A-Za-z\d_]+)/ccg/(?P<ccg_code>[A-Z\d]+)/$',
        frontend_views.measure_for_one_ccg,
        name='measure_for_one_ccg'),

    url(r'^practice/(?P<practice_code>[A-Z\d]+)/measures/$',
        frontend_views.measures_for_one_practice,
        name='measures_for_one_practice'),
    url(r'^ccg/(?P<ccg_code>[A-Z\d]+)/measures/$',
        frontend_views.measures_for_one_ccg,
        name='measures_for_one_ccg'),
    url(r'^ccg/(?P<ccg_code>[A-Z\d]+)/(?P<measure>[A-Za-z\d_]+)/$',
        frontend_views.measure_for_practices_in_ccg,
        name='measure_for_practices_in_ccg'),

    # Tariffs
    url(r'^tariff/$', frontend_views.tariff,
        name='tariff_index'),
    url(r'^tariff/(?P<code>[A-Z\d]+)/$', frontend_views.tariff,
        name='tariff'),

    # API
    url(r'^api/1.0/', include('api.urls')),

    # Docs
    url(r'^docs/(?P<doc_id>[A-Za-z\d_-]+)/$',
        frontend_views.gdoc_view,
        name='docs'),

    # Other files.
    url(r'^robots\.txt/$', TemplateView.as_view(template_name='robots.txt',
                                                content_type='text/plain')),

    # required by django-allauth
    url(r'^accounts/', include('allauth.urls')),
    url(r'^admin/', include(admin.site.urls)),

    # bookmarks
    url(r'^bookmarks/(?P<key>[0-9a-z]+)$',
        bookmark_views.login_from_key,
        name='bookmark-login'),
    url(r'^bookmarks/$',
        bookmark_views.BookmarkList.as_view(),
        name='bookmark-list'),
    url(r'^finalise_signup/$',
        frontend_views.finalise_signup,
        name='finalise-signup'),
    url(r'^newsletter_signup/$',
        TemplateView.as_view(template_name='newsletter_signup.html'),
        name='newsletter-signup'),
    # Custom verification page, overrides allauth view
    url(r"^confirm-email/$", bookmark_views.email_verification_sent,
        name="account_email_verification_sent"),

    # anymail webhooks
    url(r'^anymail/', include('anymail.urls')),

    # Redirects
    url(r'^pca/$',
        RedirectView.as_view(permanent=True,
                             pattern_name='long_term_trends')),
    url(r'^caution/$', RedirectView.as_view(
        pattern_name='faq', permanent=True)),

    # Wrong URL got published
    url(r'^measures/$', RedirectView.as_view(
        pattern_name='all_measures', permanent=True)),

    # Temporary, for tracking letter mailouts. Should change to
    # redirect post March 2018
    url(r'^(?P<ccg_code>[A-Za-z\d]{3})/$',
        frontend_views.measures_for_one_ccg,
        name='measures_for_one_ccg_tracking'),
]
