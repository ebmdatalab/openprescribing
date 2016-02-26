from rest_framework.decorators import api_view
from rest_framework.response import Response
import view_utils as utils
from frontend.models import Measure, MeasureGlobal, MeasureValue


@api_view(['GET'])
def measure_global(request, format=None):
    measure = request.query_params.get('measure', None)
    if not measure:
        return Response([])

    m = Measure.objects.get(id=measure)
    query = 'SELECT month AS date, numerator, denominator, '
    query += 'calc_value, practice_10th, practice_25th, practice_50th, '
    query += 'practice_75th, practice_90th, ccg_10th, '
    query += 'ccg_25th, ccg_50th, ccg_75th, ccg_90th '
    query += "FROM frontend_measureglobal "
    query += "WHERE measure_id=%s "
    query += "ORDER BY date"
    d = {
        'measure': {
            'name': m.name,
            'title': m.title
        },
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
    if not measure:
        return Response([])

    m = Measure.objects.get(id=measure)
    query = 'SELECT pr.month AS date, pr.numerator, pr.denominator, '
    query += 'pr.calc_value, pr.percentile, pr.cost_saving, '
    query += 'pr.practice_id, pc.name as name '
    query += "FROM frontend_measurevalue pr "
    query += "JOIN frontend_practice pc ON pr.practice_id=pc.code "
    query += "WHERE pr.measure_id=%s AND "
    for i, org in enumerate(orgs):
        if len(org) == 3:
            query += "pr.pct_id=%s "
        else:
            query += "pr.practice_id=%s "
        if (i != len(orgs)-1):
            query += ' OR '
    query += "ORDER BY date, pr.practice_id"
    d = {
        'measure': {
            'name': m.name,
            'title': m.title
        },
        'data': utils.execute_query(query, [[measure], orgs])
    }
    return Response(d)
