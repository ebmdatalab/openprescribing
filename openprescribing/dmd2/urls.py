from django.conf.urls import url

from . import views


urlpatterns = [
    url(r'^(?P<obj_type>\w+)/(?P<id>\d+)/$', views.dmd_obj_view, name="dmd_obj"),
]
