from rest_framework.decorators import api_view
from rest_framework.response import Response
import view_utils as utils
from frontend.models import Measure, MeasureGlobal, MeasureValue


@api_view(['GET'])
def measure_global(request, format=None):
    measure = request.query_params.get('measure', None)
    if measure:
        m = Measure.objects.get(id=measure)
        mdata = {
            'name': m.name,
            'title': m.title
        }
    else:
        mdata = {}

    query = 'SELECT month AS date, numerator, denominator, measure_id, '
    query += 'calc_value, practice_10th, practice_25th, practice_50th, '
    query += 'practice_75th, practice_90th, ccg_10th, '
    query += 'ccg_25th, ccg_50th, ccg_75th, ccg_90th '
    query += "FROM frontend_measureglobal "
    if measure:
        query += "WHERE measure_id=%s "
    query += "ORDER BY measure_id, date"

    d = {
        'measure': mdata,
        'data': utils.execute_query(query, [[measure]])
    }
    return Response(d)


@api_view(['GET'])
def measure_by_ccg(request, format=None):
    measure = request.query_params.get('measure', None)
    orgs = utils.param_to_list(request.query_params.get('org', []))
    if not measure:
        return Response([])

    m = Measure.objects.get(id=measure)
    d = {
        'measure': {
            'name': m.name,
            'title': m.title
        }
    }
    return Response(d)


@api_view(['GET'])
def measure_by_practice(request, format=None):
    measure = request.query_params.get('measure', None)
    orgs = utils.param_to_list(request.query_params.get('org', []))

    query = 'SELECT pr.month AS date, pr.numerator, pr.denominator, '
    query += 'pr.calc_value, pr.percentile, pr.cost_saving, '
    query += 'pr.practice_id, pc.name as name, measure_id '
    query += "FROM frontend_measurevalue pr "
    query += "JOIN frontend_practice pc ON pr.practice_id=pc.code "
    query += "WHERE "
    for i, org in enumerate(orgs):
        if len(org) == 3:
            query += "pr.pct_id=%s "
        else:
            query += "pr.practice_id=%s "
        if (i != len(orgs)-1):
            query += ' OR '
    if measure:
        query += "AND pr.measure_id=%s "
    query += "ORDER BY pr.practice_id, measure_id, date"

    if measure:
        m = Measure.objects.get(id=measure)
        d = {
            'measure': {
                'name': m.name,
                'title': m.title
            },
            'data': utils.execute_query(query, [orgs, [measure]])
        }
    else:
        d = {
            'data': utils.execute_query(query, [orgs])
        }
    return Response(d)
