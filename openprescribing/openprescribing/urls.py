from django.conf.urls import patterns, include, url
from django.conf.urls.static import static
from django.conf import settings
from django.views.generic import TemplateView
from common import utils
import api


urlpatterns = patterns(
    '',
    # Static pages.
    url(r'^$', TemplateView.as_view(template_name='index.html'), name="home"),
    url(r'^analyse/$', TemplateView.as_view(template_name='analyse.html'),
        name="analyse"),
    url(r'^api/$', TemplateView.as_view(template_name='api.html'), name="api"),
    url(r'^about/$', TemplateView.as_view(template_name='about.html'),
        name="about"),
    url(r'^caution/$', TemplateView.as_view(template_name='caution.html'), name="caution"),
    url(r'^how-to-use/$', TemplateView.as_view(template_name='how-to-use.html'),
        name="how-to-use"),

    # User-facing pages.
    url(r'^chemical/$', 'frontend.views.views.all_chemicals',
        name='all_chemicals'),
    url(r'^chemical/(?P<bnf_code>[A-Z\d]+)$', 'frontend.views.views.chemical',
        name='chemical'),
    url(r'^practice/$', 'frontend.views.views.all_practices',
        name='all_practices'),
    url(r'^practice/(?P<code>[A-Z\d]+)$', 'frontend.views.views.practice',
        name='practice'),
    url(r'^area_team/$', 'frontend.views.views.all_area_teams',
        name='all_area_teams'),
    url(r'^area_team/(?P<at_code>[A-Z\d]+)$', 'frontend.views.views.area_team',
        name='area_team'),
    url(r'^ccg/$', 'frontend.views.views.all_ccgs', name='all_ccgs'),
    url(r'^ccg/(?P<ccg_code>[A-Z\d]+)$', 'frontend.views.views.ccg',
        name='ccg'),
    url(r'^bnf/$', 'frontend.views.views.all_bnf', name='all_bnf'),
    url(r'^bnf/(?P<section_id>[\d]+)$', 'frontend.views.views.bnf_section',
        name='bnf_section'),
    url(r'^500/$', 'frontend.views.views.test_500_view',
        name='test_500'),

    url(r'^api/1.0/', include('api.urls')),

    # Other files.
    (r'^robots\.txt/$', TemplateView.as_view(template_name='robots.txt',
     content_type='text/plain')),
)

# if settings.DEBUG:
#     import debug_toolbar
#     urlpatterns += patterns('',
#                             url(r'^__debug__/', include(debug_toolbar.urls)),
#                             )
