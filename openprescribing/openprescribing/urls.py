from django.conf.urls import patterns, include, url
from django.conf.urls.static import static
from django.conf import settings
from django.views.generic import TemplateView
from common import utils
import api
from frontend.views import views as frontend_views

urlpatterns = [
    # Static pages.
    url(r'^$', TemplateView.as_view(template_name='index.html'), name="home"),
    url(r'^analyse/$', TemplateView.as_view(template_name='analyse.html'),
        name="analyse"),
    url(r'^api/$', TemplateView.as_view(template_name='api.html'), name="api"),
    url(r'^about/$', TemplateView.as_view(template_name='about.html'),
        name="about"),
    url(r'^caution/$', TemplateView.as_view(template_name='caution.html'),
        name="caution"),
    url(r'^how-to-use/$',
        TemplateView.as_view(template_name='how-to-use.html'),
        name="how-to-use"),

    # User-facing pages.
    url(r'^chemical/$', frontend_views.all_chemicals,
        name='all_chemicals'),
    url(r'^chemical/(?P<bnf_code>[A-Z\d]+)/$', frontend_views.chemical,
        name='chemical'),
    url(r'^practice/$', frontend_views.all_practices,
        name='all_practices'),
    url(r'^practice/(?P<code>[A-Z\d]+)/$', frontend_views.practice,
        name='practice'),
    url(r'^practice/(?P<code>[A-Z\d]+)/measures/$',
        frontend_views.measures_for_one_practice,
        name='measures_for_one_practice'),
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
    url(r'^ccg/(?P<ccg_code>[A-Z\d]+)/$', frontend_views.ccg,
        name='ccg'),
    url(r'^ccg/(?P<ccg_code>[A-Z\d]+)/measures/$',
        frontend_views.measures_for_one_ccg,
        name='measures_for_one_ccg'),
    url(r'^ccg/(?P<ccg_code>[A-Z\d]+)/(?P<measure>[A-Za-z\d_]+)/$',
        frontend_views.measure_for_practices_in_ccg,
        name='measure_for_practices_in_ccg'),
    url(r'^bnf/$', frontend_views.all_bnf, name='all_bnf'),
    url(r'^bnf/(?P<section_id>[\d]+)/$', frontend_views.bnf_section,
        name='bnf_section'),
    url(r'^500/$', frontend_views.test_500_view,
        name='test_500'),

    url(r'^api/1.0/', include('api.urls')),

    # Other files.
    url(r'^robots\.txt/$', TemplateView.as_view(template_name='robots.txt',
        content_type='text/plain')),
]
