from django.conf.urls import patterns, include, url
from django.conf.urls.static import static
from django.conf import settings
from django.views.generic import RedirectView, TemplateView
from django.core.urlresolvers import reverse
from common import utils
import api
from django.contrib import admin
from frontend.views import views as frontend_views
from frontend.views import profile_views
from frontend.views import bookmark_views

admin.autodiscover()

urlpatterns = [
    # Static pages.
    url(r'^$', TemplateView.as_view(template_name='index.html'), name="home"),
    url(r'^api/$', TemplateView.as_view(template_name='api.html'), name="api"),
    url(r'^about/$', TemplateView.as_view(template_name='about.html'),
        name="about"),
    url(r'^caution/$', TemplateView.as_view(template_name='caution.html'),
        name="caution"),
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
    url(r'^practice/(?P<code>[A-Z\d]+)/measures/$',
        RedirectView.as_view(permanent=True,
                             pattern_name='measures_for_one_practice'),
        name='practice'),
    url(r'^area_team/$', frontend_views.all_area_teams,
        name='all_area_teams'),
    url(r'^area_team/(?P<at_code>[A-Z\d]+)/$', frontend_views.area_team,
        name='area_team'),
    url(r'^measure/$',
        frontend_views.all_measures,
        name='all_measures'),
    url(r'^measure/(?P<measure>[A-Za-z\d_]+)/$',
        frontend_views.measure_for_all_ccgs,
        name='measure_for_all_ccgs'),
    url(r'^ccg/$', frontend_views.all_ccgs, name='all_ccgs'),
    url(r'^ccg/(?P<ccg_code>[A-Z\d]+)/$',
        frontend_views.measures_for_one_ccg,
        name='measures_for_one_ccg'),
    url(r'^ccg/(?P<code>[A-Z\d]+)/preview_bookmark/$',
        bookmark_views.preview_ccg_bookmark,
        name='preview-ccg-bookmark'),
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
    url(r'^500/$', frontend_views.test_500_view,
        name='test_500'),

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

    # anymail webhooks
    url(r'^anymail/', include('anymail.urls')),
]
