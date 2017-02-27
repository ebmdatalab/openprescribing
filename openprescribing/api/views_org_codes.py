from rest_framework.decorators import api_view
from rest_framework.response import Response
import view_utils as utils
from django.db.models import Q
from frontend.models import PCT, Practice


@api_view(['GET'])
def org_codes(request, format=None):
    org_codes = utils.param_to_list(request.query_params.get('q', None))
    org_types = utils.param_to_list(request.query_params.get('org_type', None))
    is_exact = request.GET.get('exact', '')
    if not org_types:
        org_types = ['']
    if not org_codes:
        org_codes = ['']
    data = []
    for org_code in org_codes:
        for org_type in org_types:
            data += _get_org_from_code(org_code, is_exact, org_type)
    return Response(data)


def _get_org_from_code(q, is_exact, org_type):
    if is_exact:
        if len(q) == 3:
            results = PCT.objects.filter(Q(code=q) | Q(name=q)) \
                                 .filter(org_type='CCG')
            values = results.values('name', 'code')
            for v in values:
                v['id'] = v['code']
                v['type'] = 'CCG'
        else:
            results = Practice.objects.filter(Q(code=q) | Q(name=q))
            values = results.values('name', 'code', 'ccg')
            for v in values:
                v['id'] = v['code']
                v['type'] = 'practice'
    else:
        values = []
        if org_type == 'practice':
            values += _get_practices_like_code(q)
        elif org_type == 'CCG':
            values += _get_pcts_like_code(q)
        else:
            values += _get_pcts_like_code(q)
            values += _get_practices_like_code(q)
    return values


def _get_practices_like_code(q):
    if q:
        practices = Practice.objects.filter(Q(code__istartswith=q) |
                                            Q(name__icontains=q))
    else:
        practices = Practice.objects.all()
    results = []
    for p in practices:
        data = {
            'id': p.code,
            'code': p.code,
            'name': p.name,
            'setting': p.setting,
            'setting_name': None,
            'type': 'Practice',
            'ccg': None
        }
        data['setting_name'] = p.get_setting_display()
        if p.ccg:
            data['ccg'] = p.ccg.code
        results.append(data)
    return results


def _get_pcts_like_code(q):
    if q:
        pcts = PCT.objects.filter(Q(code__istartswith=q) |
                                  Q(name__icontains=q)) \
                          .filter(org_type='CCG')
    else:
        pcts = PCT.objects.all()
    pct_values = pcts.values('name', 'code')
    for p in pct_values:
        p['id'] = p['code']
        p['type'] = 'CCG'
    return pct_values
