from django.urls import path

from . import views

urlpatterns = [
    path(r"", views.search_view, name="dmd_search"),
    path(r"<obj_type>/<int:id>/", views.dmd_obj_view, name="dmd_obj"),
    path(
        r"vmp/<vmp_id>/relationships/",
        views.vmp_relationships_view,
        name="vmp_relationships",
    ),
    path(
        r"bnf/<bnf_code>/relationships/",
        views.bnf_code_relationships_view,
        name="bnf_code_relationships",
    ),
    path(
        r"advanced-search/<obj_type>/",
        views.advanced_search_view,
        name="dmd_advanced_search",
    ),
    path(
        r"search-filters/<obj_type>/",
        views.search_filters_view,
        name="dmd_search_filters",
    ),
]
