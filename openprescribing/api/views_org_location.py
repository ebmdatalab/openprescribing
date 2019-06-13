from django.http import HttpResponse
from django.contrib.gis.db.models.aggregates import Union

from rest_framework.decorators import api_view

from frontend.models import PCT, Practice, STP, RegionalTeam
from api.geojson_serializer import as_geojson_stream
import api.view_utils as utils


@api_view(['GET'])
def org_location(request, format=None):
    org_type = request.GET.get('org_type', '')
    centroids = request.GET.get('centroids', '')
    org_codes = utils.param_to_list(request.GET.get('q', ''))
    if org_type == 'practice':
        result_spec = _get_practices(org_codes, centroids)
    elif org_type == 'ccg':
        result_spec = _get_ccgs(org_codes, centroids)
    elif org_type == 'stp':
        result_spec = _get_stps(org_codes, centroids)
    elif org_type == 'regional_team':
        result_spec = _get_regional_teams(org_codes, centroids)
    else:
        raise ValueError('Unknown org_type: {}'.format(org_type))
    results, geo_field, other_fields = result_spec
    fields = other_fields + (geo_field,)
    return HttpResponse(
        as_geojson_stream(results.values(*fields), geometry_field=geo_field),
        content_type='application/json'
    )


def _get_practices(org_codes, centroids):
    org_codes = utils.get_practice_ids_from_org(org_codes)
    results = Practice.objects.filter(code__in=org_codes)
    geo_field = 'location'
    other_fields = ('name', 'code', 'setting', 'is_dispensing')
    return results, geo_field, other_fields


def _get_ccgs(org_codes, centroids):
    results = PCT.objects.filter(close_date__isnull=True, org_type='CCG')
    if org_codes:
        results = results.filter(code__in=org_codes)
    geo_field = 'centroid' if centroids else 'boundary'
    other_fields = ('name', 'code', 'ons_code', 'org_type')
    return results, geo_field, other_fields


def _get_stps(org_codes, centroids):
    results = STP.objects.all()
    if org_codes:
        results = results.filter(ons_code__in=org_codes)
    results = results.annotate(boundary=Union('pct__boundary'))
    geo_field = 'boundary'
    other_fields = ('name', 'ons_code')
    return results, geo_field, other_fields


def _get_regional_teams(org_codes, centroids):
    results = RegionalTeam.objects.filter(close_date__isnull=True)
    if org_codes:
        results = results.filter(code__in=org_codes)
    results = results.annotate(boundary=Union('pct__boundary'))
    geo_field = 'boundary'
    other_fields = ('name', 'code')
    return results, geo_field, other_fields
