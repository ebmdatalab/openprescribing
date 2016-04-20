from rest_framework.decorators import api_view
from rest_framework.response import Response
import view_utils as utils
from frontend.models import Measure, MeasureGlobal, MeasureValue

@api_view(['GET'])
def measure_global(request, format=None):
    measure = request.query_params.get('measure', None)

    query = 'SELECT mg.month AS date, mg.numerator, mg.denominator, mg.measure_id, '
    query += 'mg.calc_value, practice_10th, mg.practice_25th, mg.practice_50th, '
    query += 'mg.practice_75th, mg.practice_90th, mg.ccg_10th, '
    query += 'mg.ccg_25th, mg.ccg_50th, mg.ccg_75th, mg.ccg_90th, '
    query += 'mg.cost_saving_10th, mg.cost_saving_25th, mg.cost_saving_50th, '
    query += 'mg.cost_saving_75th, mg.cost_saving_90th, '
    query += 'ms.name, ms.title, ms.description, ms.numerator_description, '
    query += 'ms.denominator_description, ms.denominator_short, ms.numerator_short, '
    query += 'ms.url, ms.is_cost_based '
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
            'practice_10th': d['practice_10th'],
            'practice_25th': d['practice_25th'],
            'practice_50th': d['practice_50th'],
            'practice_75th': d['practice_75th'],
            'practice_90th': d['practice_90th'],
            'ccg_10th': d['ccg_10th'],
            'ccg_25th': d['ccg_25th'],
            'ccg_50th': d['ccg_50th'],
            'ccg_75th': d['ccg_75th'],
            'ccg_90th': d['ccg_90th'],
            'cost_saving_10th': d['cost_saving_10th'],
            'cost_saving_25th': d['cost_saving_25th'],
            'cost_saving_50th': d['cost_saving_50th'],
            'cost_saving_75th': d['cost_saving_75th'],
            'cost_saving_90th': d['cost_saving_90th']
        }
        if id in rolled:
            rolled[id]['data'].append(d_copy)
        else:
            rolled[id] = {
                'id': id,
                'name': d['name'],
                'title': d['title'],
                'description': d['description'],
                'numerator_description': d['numerator_description'],
                'denominator_description': d['denominator_description'],
                'numerator_short': d['numerator_short'],
                'denominator_short': d['denominator_short'],
                'url': d['url'],
                'is_cost_based': d['is_cost_based'],
                'data': [d_copy]
            }
    d = {
        'measures': [rolled[k] for k in rolled]
    }
    return Response(d)


@api_view(['GET'])
def measure_by_ccg(request, format=None):
    measure = request.query_params.get('measure', None)
    orgs = utils.param_to_list(request.query_params.get('org', []))

    query = 'SELECT mv.month AS date, mv.numerator, mv.denominator, '
    query += 'mv.calc_value, mv.percentile, mv.cost_saving_10th, '
    query += 'mv.cost_saving_25th, mv.cost_saving_50th, '
    query += 'mv.cost_saving_75th, mv.cost_saving_90th, '
    query += 'mv.pct_id, pc.name as pct_name, measure_id, '
    query += 'ms.name, ms.title, ms.description, ms.numerator_description, '
    query += 'ms.denominator_description, ms.denominator_short, ms.numerator_short, '
    query += 'ms.url, ms.is_cost_based '
    query += "FROM frontend_measurevalue mv "
    query += "JOIN frontend_pct pc ON mv.pct_id=pc.code "
    query += "JOIN frontend_measure ms ON mv.measure_id=ms.id "
    query += "WHERE "
    if orgs:
        query += "("
    for i, org in enumerate(orgs):
        query += "mv.pct_id=%s "
        if (i != len(orgs)-1):
            query += ' OR '
    if orgs:
        query += ") AND "
    query += 'mv.practice_id IS NULL '
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
            'cost_saving_10th': d['cost_saving_10th'],
            'cost_saving_25th': d['cost_saving_25th'],
            'cost_saving_50th': d['cost_saving_50th'],
            'cost_saving_75th': d['cost_saving_75th'],
            'cost_saving_90th': d['cost_saving_90th'],
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
                'numerator_description': d['numerator_description'],
                'denominator_description': d['denominator_description'],
                'numerator_short': d['numerator_short'],
                'denominator_short': d['denominator_short'],
                'url': d['url'],
                'is_cost_based': d['is_cost_based'],
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

    query = 'SELECT mv.month AS date, mv.numerator, mv.denominator, '
    query += 'mv.calc_value, mv.percentile, mv.cost_saving_10th, '
    query += 'mv.cost_saving_25th, mv.cost_saving_50th, '
    query += 'mv.cost_saving_75th, mv.cost_saving_90th, '
    query += 'mv.practice_id, pc.name as practice_name, measure_id, '
    query += 'ms.name, ms.title, ms.description, ms.numerator_description, '
    query += 'ms.denominator_description, ms.denominator_short, ms.numerator_short, '
    query += 'ms.url, ms.is_cost_based '
    query += "FROM frontend_measurevalue mv "
    query += "JOIN frontend_practice pc ON mv.practice_id=pc.code "
    query += "JOIN frontend_measure ms ON mv.measure_id=ms.id "
    query += "WHERE "
    for i, org in enumerate(orgs):
        if len(org) == 3:
            query += "mv.pct_id=%s "
        else:
            query += "mv.practice_id=%s "
        if (i != len(orgs)-1):
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
            'cost_saving_10th': d['cost_saving_10th'],
            'cost_saving_25th': d['cost_saving_25th'],
            'cost_saving_50th': d['cost_saving_50th'],
            'cost_saving_75th': d['cost_saving_75th'],
            'cost_saving_90th': d['cost_saving_90th'],
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
                'numerator_description': d['numerator_description'],
                'denominator_description': d['denominator_description'],
                'numerator_short': d['numerator_short'],
                'denominator_short': d['denominator_short'],
                'url': d['url'],
                'is_cost_based': d['is_cost_based'],
                'data': [d_copy]
            }

    d = {
        'measures': [rolled[k] for k in rolled]
    }
    return Response(d)
