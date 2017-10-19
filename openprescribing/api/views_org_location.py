from rest_framework.decorators import api_view
from rest_framework.response import Response
from frontend.models import PCT, Practice
import view_utils as utils
from django.http import HttpResponse
from django.core.serializers import serialize


@api_view(['GET'])
def org_location(request, format=None):
    org_type = request.GET.get('org_type', '')
    org_codes = utils.param_to_list(request.GET.get('q', ''))
    if org_type == 'practice':
        org_codes = utils.get_practice_ids_from_org(org_codes)
    if org_type == 'ccg':
        results = PCT.objects.filter(close_date__isnull=True) \
                             .filter(org_type='CCG')
        if org_codes:
            results = results.filter(code__in=org_codes)
        geo_field = 'boundary'
        fields = (
            'name',
            'code',
            'ons_code',
            'org_type',
            'boundary',
        )
    else:
        results = Practice.objects.filter(code__in=org_codes)
        geo_field = 'location'
        fields = (
            'name',
            'code',
            'setting',
            'is_dispensing',
            'location',
        )
    return HttpResponse(
        serialize('geojson', results, geometry_field=geo_field, fields=fields),
        content_type='application/json')
