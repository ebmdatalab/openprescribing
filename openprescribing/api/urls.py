from django.conf.urls import url, include
from rest_framework import routers
from rest_framework.urlpatterns import format_suffix_patterns
import views_bnf_codes
import views_spending
import views_org_codes
import views_org_details
import views_org_location
import views_measures


urlpatterns = [
    url(r'^spending/$', views_spending.total_spending,
        name='total_spending'),
    url(r'^bubble/$', views_spending.bubble,
        name='bubble'),
    url(r'^spending_by_ccg/$', views_spending.spending_by_ccg,
        name='spending_by_ccg'),
    url(r'^spending_by_practice/$', views_spending.spending_by_practice,
        name='spending_by_practice'),
    url(r'^measure/$', views_measures.measure_global,
        name='measure'),
    url(r'^measure_by_ccg/$', views_measures.measure_by_ccg,
        name='measure_by_ccg'),
    url(r'^measure_numerators_by_ccg/$', views_measures.measure_numerators_by_ccg,
        name='measure_numerators_by_ccg'),
    url(r'^measure_by_practice/$', views_measures.measure_by_practice,
        name='measure_by_practice'),
    url(r'^price_per_unit/$', views_spending.price_per_unit,
        name='price_per_unit_api'),
    url(r'^org_details/$', views_org_details.org_details),
    url(r'^bnf_code/$', views_bnf_codes.bnf_codes),
    url(r'^org_code/$', views_org_codes.org_codes),
    url(r'^org_location/$', views_org_location.org_location),
    url(r'^docs/', include('rest_framework_swagger.urls')),
]

urlpatterns = format_suffix_patterns(urlpatterns,
                                     allowed=['json', 'csv'])
