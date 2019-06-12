from django.http import HttpResponse
from django.core.serializers import serialize

from rest_framework.decorators import api_view

from frontend.models import PCT, Practice
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
    else:
        raise ValueError('Unknown org_type: {}'.format(org_type))
    results, geo_field, other_fields = result_spec
    fields = other_fields + (geo_field,)
    return HttpResponse(
        serialize('geojson', results, geometry_field=geo_field, fields=fields),
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
