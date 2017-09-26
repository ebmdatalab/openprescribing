import json
import os

from rest_framework.decorators import api_view
from rest_framework.exceptions import APIException
from rest_framework.response import Response

from frontend.models import ImportLog
from frontend.models import Measure
from common.utils import get_columns_for_select

import view_utils as utils


class MissingParameter(APIException):
    status_code = 400
    default_detail = 'You are missing a required parameter.'


@api_view(['GET'])
def measure_global(request, format=None):
    measure = request.query_params.get('measure', None)

    query = 'SELECT mg.month AS date, mg.numerator,  '
    query += 'mg.denominator, mg.measure_id, '
    query += 'mg.calc_value, mg.percentiles, mg.cost_savings, '
    query += 'ms.name, ms.title, ms.description, '
    query += 'ms.why_it_matters, '
    query += ' ms.denominator_short, ms.numerator_short, '
    query += 'ms.url, ms.is_cost_based, ms.is_percentage, '
    query += 'ms.low_is_good '
    query += "FROM frontend_measureglobal mg "
    query += "JOIN frontend_measure ms ON mg.measure_id=ms.id "
    if measure:
        query += "WHERE mg.measure_id=%s "
    query += "ORDER BY mg.measure_id, mg.month"

    data = utils.execute_query(query, [[measure]])
    rolled = {}
    for d in data:
        id = d['measure_id']
        d_copy = {
            'date': d['date'],
            'numerator': d['numerator'],
            'denominator': d['denominator'],
            'calc_value': d['calc_value'],
            'percentiles': d['percentiles'],
            'cost_savings': d['cost_savings']
        }
        if id in rolled:
            rolled[id]['data'].append(d_copy)
        else:
            rolled[id] = {
                'id': id,
                'name': d['name'],
                'title': d['title'],
                'description': d['description'],
                'why_it_matters': d['why_it_matters'],
                'numerator_short': d['numerator_short'],
                'denominator_short': d['denominator_short'],
                'url': d['url'],
                'is_cost_based': d['is_cost_based'],
                'is_percentage': d['is_percentage'],
                'low_is_good': d['low_is_good'],
                'data': [d_copy]
            }
    d = {
        'measures': [rolled[k] for k in rolled]
    }
    return Response(d)

def _getMeasureData(measure):
    fpath = os.path.dirname(__file__)
    fname = os.path.join(fpath, "../frontend/management/commands/measure_definitions/%s.json" % measure)
    return json.load(open(fname, 'r'))


@api_view(['GET'])
def measure_numerators_by_org(request, format=None):
    # XXX assert hscic.normalised_prescribing_standard is in the
    # numerator_from, or use another flag in the measure definition
    # (e.g. LP omnibus can't easily be broken down)
    measure = request.query_params.get('measure', None)
    org = utils.param_to_list(request.query_params.get('org', []))[0]
    if len(org) == 3:
        org_selector = 'pct_id'
    else:
        org_selector = 'practice_id'
    this_month = ImportLog.objects.latest_in_category('prescribing').current_at
    m = _getMeasureData(measure)
    query = ('SELECT '
             '  %s AS entity, '
             '  presentation_code AS bnf_code, '
             '  COALESCE(dmd.name, p.name) AS presentation_name, '
             "  SUM(total_items) AS total_items, "
             "  SUM(actual_cost) AS cost, "
             "  SUM(quantity) AS quantity, "
             '  %s '
             'FROM '
             '  frontend_prescription pr '
             'LEFT JOIN '
             '  dmd_product dmd '
             'ON pr.presentation_code = dmd.bnf_code '
             'INNER JOIN '
             '  frontend_presentation p '
             'ON pr.presentation_code = p.bnf_code '
             'WHERE '
             "  %s = '%s' "
             '  AND '
             "  processing_date = '%s' "
             '  AND (%s) '
             'GROUP BY '
             '  %s, presentation_code, dmd.name, p.name '
             'ORDER BY numerator DESC '
             'LIMIT 50') % (
                 org_selector,
                 " ".join(get_columns_for_select(m, 'numerator')).replace('items', 'total_items'),
                 org_selector,
                 org, this_month.strftime('%Y-%m-%d'),
                 " ".join(m['numerator_where']).replace('bnf_code', 'presentation_code'),
                 org_selector
             )
    data = utils.execute_query(query, [])
    return Response(data)

@api_view(['GET'])
def measure_by_ccg(request, format=None):
    measure = request.query_params.get('measure', None)
    orgs = utils.param_to_list(request.query_params.get('org', []))

    query = 'SELECT mv.month AS date, mv.numerator, mv.denominator, '
    query += 'mv.calc_value, mv.percentile, mv.cost_savings, '
    query += 'mv.pct_id, pc.name as pct_name, measure_id, '
    query += 'ms.name, ms.title, ms.description, '
    query += 'ms.why_it_matters, ms.denominator_short, '
    query += 'ms.numerator_short, '
    query += 'ms.url, ms.is_cost_based, ms.is_percentage, '
    query += 'ms.low_is_good '
    query += "FROM frontend_measurevalue mv "
    query += "JOIN frontend_pct pc ON "
    query += "(mv.pct_id=pc.code AND pc.org_type = 'CCG') "
    query += "JOIN frontend_measure ms ON mv.measure_id=ms.id "
    query += "WHERE pc.close_date IS NULL AND "
    if orgs:
        query += "("
    for i, org in enumerate(orgs):
        query += "mv.pct_id=%s "
        if (i != len(orgs) - 1):
            query += ' OR '
    if orgs:
        query += ") AND "
    query += 'mv.practice_id IS NULL '
    if measure:
        query += "AND mv.measure_id=%s "
    query += "ORDER BY mv.pct_id, measure_id, date"

    if measure:
        data = utils.execute_query(query, [orgs, [measure]])
    else:
        data = utils.execute_query(query, [orgs])

    rolled = {}
    for d in data:
        id = d['measure_id']
        d_copy = {
            'date': d['date'],
            'numerator': d['numerator'],
            'denominator': d['denominator'],
            'calc_value': d['calc_value'],
            'percentile': d['percentile'],
            'cost_savings': d['cost_savings'],
            'pct_id': d['pct_id'],
            'pct_name': d['pct_name']
        }
        if id in rolled:
            rolled[id]['data'].append(d_copy)
        else:
            rolled[id] = {
                'id': id,
                'name': d['name'],
                'title': d['title'],
                'description': d['description'],
                'why_it_matters': d['why_it_matters'],
                'numerator_short': d['numerator_short'],
                'denominator_short': d['denominator_short'],
                'url': d['url'],
                'is_cost_based': d['is_cost_based'],
                'is_percentage': d['is_percentage'],
                'low_is_good': d['low_is_good'],
                'data': [d_copy]
            }

    d = {
        'measures': [rolled[k] for k in rolled]
    }
    return Response(d)


@api_view(['GET'])
def measure_by_practice(request, format=None):
    measure = request.query_params.get('measure', None)
    orgs = utils.param_to_list(request.query_params.get('org', []))
    if not orgs:
        raise MissingParameter
    query = 'SELECT mv.month AS date, mv.numerator, mv.denominator, '
    query += 'mv.calc_value, mv.percentile, mv.cost_savings, '
    query += 'mv.practice_id, pc.name as practice_name, measure_id, '
    query += 'ms.name, ms.title, ms.description, ms.why_it_matters, '
    query += 'ms.denominator_short, ms.numerator_short, '
    query += 'ms.url, ms.is_cost_based, ms.is_percentage, '
    query += 'ms.low_is_good '
    query += "FROM frontend_measurevalue mv "
    query += "JOIN frontend_practice pc ON mv.practice_id=pc.code "
    query += "JOIN frontend_measure ms ON mv.measure_id=ms.id "
    query += "WHERE "
    for i, org in enumerate(orgs):
        if len(org) == 3:
            query += "mv.pct_id=%s "
        else:
            query += "mv.practice_id=%s "
        if (i != len(orgs) - 1):
            query += ' OR '
    if measure:
        query += "AND mv.measure_id=%s "
    query += "ORDER BY mv.practice_id, measure_id, date"

    if measure:
        data = utils.execute_query(query, [orgs, [measure]])
    else:
        data = utils.execute_query(query, [orgs])

    rolled = {}
    for d in data:
        id = d['measure_id']
        d_copy = {
            'date': d['date'],
            'numerator': d['numerator'],
            'denominator': d['denominator'],
            'calc_value': d['calc_value'],
            'percentile': d['percentile'],
            'cost_savings': d['cost_savings'],
            'practice_id': d['practice_id'],
            'practice_name': d['practice_name']
        }
        if id in rolled:
            rolled[id]['data'].append(d_copy)
        else:
            rolled[id] = {
                'id': id,
                'name': d['name'],
                'title': d['title'],
                'description': d['description'],
                'why_it_matters': d['why_it_matters'],
                'numerator_short': d['numerator_short'],
                'denominator_short': d['denominator_short'],
                'url': d['url'],
                'is_cost_based': d['is_cost_based'],
                'is_percentage': d['is_percentage'],
                'low_is_good': d['low_is_good'],
                'data': [d_copy]
            }

    d = {
        'measures': [rolled[k] for k in rolled]
    }
    return Response(d)
