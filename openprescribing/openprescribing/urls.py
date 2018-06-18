from django.conf.urls import include, url
from django.views.generic import RedirectView, TemplateView
from django.contrib import admin
from frontend.views import views as frontend_views
from frontend.views import bookmark_views

admin.autodiscover()

handler500 = frontend_views.custom_500

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
    url(r'^pca/$',
        RedirectView.as_view(permanent=True,
                             pattern_name='long_term_trends')),
    url(r'^price-per-unit-faq/$', TemplateView.as_view(
        template_name='price_per_unit_faq.html'),
        name="price_per_unit_faq"),
    url(r'^contact/$', TemplateView.as_view(template_name='contact.html'),
        name="contact"),
    url(r'^how-to-use/$',
        TemplateView.as_view(template_name='how-to-use.html'),
        name="how-to-use"),

    # User-facing pages.
    url(r'^analyse/$', frontend_views.analyse,
        name="analyse"),
    url(r'^chemical/$', frontend_views.all_chemicals,
        name='all_chemicals'),
    url(r'^chemical/(?P<bnf_code>[A-Z\d]+)/$', frontend_views.chemical,
        name='chemical'),
    url(r'^practice/$', frontend_views.all_practices,
        name='all_practices'),
    url(r'^practice/(?P<code>[A-Z\d]+)/$',
        frontend_views.measures_for_one_practice,
        name='measures_for_one_practice'),
    url(r'^practice/(?P<code>[A-Z\d]+)/preview_bookmark/$',
        bookmark_views.preview_practice_bookmark,
        name='preview-practice-bookmark'),
    url(r'^practice/(?P<code>[A-Z\d]+)/price_per_unit/$',
        frontend_views.practice_price_per_unit,
        name='practice_price_per_unit'),
    url(r'^practice/(?P<entity_code>[A-Z\d]+)/'
        '(?P<bnf_code>[A-Z\d]+)/price_per_unit/$',
        frontend_views.price_per_unit_by_presentation,
        name='price_per_unit_by_presentation_practice'),
    url(r'^measure/$',
        frontend_views.all_measures,
        name='all_measures'),
    url(r'^measure/(?P<measure>[A-Za-z\d_]+)/$',
        frontend_views.measure_for_all_ccgs,
        name='measure_for_all_ccgs'),
    url(r'^measure/(?P<measure>[A-Za-z\d_]+)/ccg/(?P<ccg_code>[A-Z\d]+)/$',
        frontend_views.measure_for_one_ccg,
        name='measure_for_one_ccg'),
    url(r'^measure/(?P<measure>[A-Za-z\d_]+)/'
        'practice/(?P<practice_code>[A-Z\d]+)/$',
        frontend_views.measure_for_one_practice,
        name='measure_for_one_practice'),
    url(r'^ccg/$', frontend_views.all_ccgs, name='all_ccgs'),
    url(r'^ccg/(?P<ccg_code>[A-Z\d]+)/$',
        frontend_views.measures_for_one_ccg,
        name='measures_for_one_ccg'),
    url(r'^ccg/(?P<code>[A-Z\d]+)/preview_bookmark/$',
        bookmark_views.preview_ccg_bookmark,
        name='preview-ccg-bookmark'),
    url(r'^ccg/(?P<code>[A-Z\d]+)/price_per_unit/$',
        frontend_views.ccg_price_per_unit,
        name='ccg_price_per_unit'),
    url(r'^ccg/(?P<entity_code>[A-Z\d]+)/'
        '(?P<bnf_code>[A-Z\d]+)/price_per_unit/$',
        frontend_views.price_per_unit_by_presentation,
        name='price_per_unit_by_presentation'),
    url(r'^ccg/(?P<ccg_code>[A-Z\d]+)/measures/$',
        RedirectView.as_view(permanent=True,
                             pattern_name='measures_for_one_ccg'),
        name='ccg'),
    url(r'^ccg/(?P<ccg_code>[A-Z\d]+)/(?P<measure>[A-Za-z\d_]+)/$',
        frontend_views.measure_for_practices_in_ccg,
        name='measure_for_practices_in_ccg'),
    url(r'^bnf/$', frontend_views.all_bnf, name='all_bnf'),
    url(r'^bnf/(?P<section_id>[\d]+)/$', frontend_views.bnf_section,
        name='bnf_section'),
    url(r'^tariff/$', frontend_views.tariff,
        name='tariff_index'),
    url(r'^tariff/(?P<code>[A-Z\d]+)/$', frontend_views.tariff,
        name='tariff'),
    url(r'^api/1.0/', include('api.urls')),

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
    url(r'^last_bookmark/$',
        frontend_views.last_bookmark,
        name='last-bookmark'),
    url(r'^analyse/preview/$', bookmark_views.preview_analysis_bookmark,
        name="preview-analyse-bookmark"),
    # Custom verification page, overrides allauth view
    url(r"^confirm-email/$", bookmark_views.email_verification_sent,
        name="account_email_verification_sent"),

    # anymail webhooks
    url(r'^anymail/', include('anymail.urls')),

    # old page redirects
    url(r'^caution/$', RedirectView.as_view(
        pattern_name='faq', permanent=True)),
    url(r'^practice/(?P<code>[A-Z\d]+)/measures/$',
        RedirectView.as_view(
            permanent=True, pattern_name='measures_for_one_practice'),
        name='practice'),

    # Wrong URL got published
    url(r'^measures/$', RedirectView.as_view(
        pattern_name='all_measures', permanent=True)),

    # Temporary, for tracking letter mailouts. Should change to
    # redirect post March 2018
    url(r'^(?P<ccg_code>[A-Za-z\d]{3})/$',
        frontend_views.measures_for_one_ccg,
        name='measures_for_one_ccg_tracking'),

]
