from django.urls import path
from rest_framework.urlpatterns import format_suffix_patterns

from . import (
    views_bnf_codes,
    views_measures,
    views_org_codes,
    views_org_details,
    views_org_location,
    views_spending,
)

urlpatterns = [
    path(r"spending/", views_spending.spending_by_org, name="total_spending"),
    path(r"bubble/", views_spending.bubble, name="bubble"),
    path(r"tariff/", views_spending.tariff, name="tariff_api"),
    path(
        r"spending_by_sicbl/",
        views_spending.spending_by_org,
        name="spending_by_ccg",
        kwargs={"org_type": "ccg"},
    ),
    path(
        r"spending_by_practice/",
        views_spending.spending_by_org,
        name="spending_by_practice",
        kwargs={"org_type": "practice"},
    ),
    path(r"spending_by_org/", views_spending.spending_by_org, name="spending_by_org"),
    path(r"measure/", views_measures.measure_global, name="measure"),
    path(r"measure_by_icb/", views_measures.measure_by_stp, name="measure_by_stp"),
    path(
        r"measure_by_regional_team/",
        views_measures.measure_by_regional_team,
        name="measure_by_regional_team",
    ),
    path(r"measure_by_sicbl/", views_measures.measure_by_ccg, name="measure_by_ccg"),
    path(r"measure_by_pcn/", views_measures.measure_by_pcn, name="measure_by_pcn"),
    path(
        r"measure_numerators_by_org/",
        views_measures.measure_numerators_by_org,
        name="measure_numerators_by_org",
    ),
    path(
        r"measure_by_practice/",
        views_measures.measure_by_practice,
        name="measure_by_practice",
    ),
    path(r"price_per_unit/", views_spending.price_per_unit, name="price_per_unit_api"),
    path(r"ghost_generics/", views_spending.ghost_generics, name="ghost_generics_api"),
    path(r"org_details/", views_org_details.org_details),
    path(r"bnf_code/", views_bnf_codes.bnf_codes),
    path(r"org_code/", views_org_codes.org_codes),
    path(r"org_location/", views_org_location.org_location, name="org_location"),
]

urlpatterns = format_suffix_patterns(urlpatterns, allowed=["json", "csv"])
