from django.conf.urls import url

from . import views


urlpatterns = [
    url(r'^$', views.search_view, name="search"),
    url(r'^(?P<obj_type>\w+)/(?P<id>\d+)/$', views.dmd_obj_view, name="dmd_obj"),
    url(r'^vmp/(?P<vmp_id>\d+)/relationships/$', views.vmp_relationships_view, name="vmp_relationships"),
    url(r'^bnf/(?P<bnf_code>\w+)/relationships/$', views.bnf_code_relationships_view, name="bnf_code_relationships"),
]
