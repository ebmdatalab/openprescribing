from rest_framework.decorators import api_view
from rest_framework.response import Response
import view_utils as utils
from django.db.models import Q
from frontend.models import PCT, Practice, STP, RegionalTeam

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
        # Both regional teams and CCGs have 3 character codes, but I don't want
        # to change the API to require org_type because I don't know what else
        # might break
        if len(q) == 3 and org_type != 'regional_team':
            results = PCT.objects.filter(Q(code=q) | Q(name=q)) \
                                 .filter(org_type='CCG')
            values = results.values('name', 'code')
            for v in values:
                v['id'] = v['code']
                v['type'] = 'CCG'
        elif org_type == 'stp':
            values = _get_stps_like_code(q, is_exact=True)
        elif org_type == 'regional_team':
            values = _get_regional_teams_like_code(q, is_exact=True)
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
        elif org_type == 'stp':
            values += _get_stps_like_code(q)
        elif org_type == 'regional_team':
            values += _get_regional_teams_like_code(q)
        else:
            values += _get_pcts_like_code(q)
            values += _get_practices_like_code(q)
    return values


def _get_practices_like_code(q):
    if q:
        practices = Practice.objects.filter(
            Q(setting=4) & Q(status_code='A') & (
                Q(code__istartswith=q) |
                Q(name__icontains=q) | Q(postcode__istartswith=q))).order_by('name')
    else:
        practices = Practice.objects.all()
    results = []
    for p in practices:
        data = {
            'id': p.code,
            'code': p.code,
            'name': p.name,
            'postcode': p.postcode,
            'setting': p.setting,
            'setting_name': None,
            'type': 'practice',
            'ccg': None
        }
        data['setting_name'] = p.get_setting_display()
        if p.ccg:
            data['ccg'] = p.ccg.code
        results.append(data)
    return results


def _get_pcts_like_code(q):
    pcts = PCT.objects.filter(close_date__isnull=True)
    if q:
        pcts = pcts.filter(Q(code__istartswith=q) |
                           Q(name__icontains=q)) \
                        .filter(org_type='CCG')
    pct_values = pcts.values('name', 'code')
    for p in pct_values:
        p['id'] = p['code']
        p['type'] = 'CCG'
    return pct_values


def _get_stps_like_code(q, is_exact=False):
    orgs = STP.objects.all()
    if is_exact:
        orgs = orgs.filter(
            Q(ons_code=q) | Q(name=q)
        )
    elif q:
        orgs = orgs.filter(
            Q(ons_code__istartswith=q) | Q(name__icontains=q)
        )
    org_values = orgs.values('name', 'ons_code')
    for org in org_values:
        org['code'] = org.pop('ons_code')
        org['id'] = org['code']
        org['type'] = 'stp'
    return org_values


def _get_regional_teams_like_code(q, is_exact=False):
    orgs = RegionalTeam.objects.active()
    if is_exact:
        orgs = orgs.filter(
            Q(code=q) | Q(name=q)
        )
    elif q:
        orgs = orgs.filter(
            Q(code__istartswith=q) | Q(name__icontains=q)
        )
    org_values = orgs.values('name', 'code')
    for org in org_values:
        org['id'] = org['code']
        org['type'] = 'regional_team'
    return org_values
