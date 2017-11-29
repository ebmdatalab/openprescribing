from dateutil.relativedelta import relativedelta

from rest_framework.decorators import api_view
from rest_framework.exceptions import APIException
from rest_framework.response import Response

from frontend.models import ImportLog
from frontend.models import Measure
from frontend.models import MeasureGlobal

import view_utils as utils


class MissingParameter(APIException):
    status_code = 400
    default_detail = 'You are missing a required parameter.'


@api_view(['GET'])
def measure_global(request, format=None):
    measure = request.query_params.get('measure', None)
    tags = [x for x in request.query_params.get('tags', '').split(',') if x]
    qs = MeasureGlobal.objects.select_related('measure')
    if measure:
        qs = qs.filter(measure_id=measure)
    if tags:
        qs = qs.filter(measure__tags__overlap=tags)
    qs = qs.order_by('measure_id', 'month')
    rolled = {}
    for mg in qs:
        id = mg.measure_id
        d_copy = {
            'date': mg.month,
            'numerator': mg.numerator,
            'denominator': mg.denominator,
            'calc_value': mg.calc_value,
            'percentiles': mg.percentiles,
            'cost_savings': mg.cost_savings
        }
        if id in rolled:
            rolled[id]['data'].append(d_copy)
        else:
            measure = mg.measure
            if measure.tags_focus:
                tags_focus = ','.join(measure.tags_focus)
            else:
                tags_focus = ''
            rolled[id] = {
                'id': id,
                'name': measure.name,
                'title': measure.title,
                'description': measure.description,
                'why_it_matters': measure.why_it_matters,
                'numerator_short': measure.numerator_short,
                'denominator_short': measure.denominator_short,
                'url': measure.url,
                'is_cost_based': measure.is_cost_based,
                'is_percentage': measure.is_percentage,
                'low_is_good': measure.low_is_good,
                'tags_focus': tags_focus,
                'numerator_can_be_queried': measure.numerator_can_be_queried(),
                'data': [d_copy]
            }
    d = {
        'measures': [rolled[k] for k in rolled]
    }

    return Response(d)


@api_view(['GET'])
def measure_numerators_by_org(request, format=None):
    measure = request.query_params.get('measure', None)
    org = utils.param_to_list(request.query_params.get('org', []))[0]
    if len(org) == 3:
        org_selector = 'pct_id'
    else:
        org_selector = 'practice_id'
    this_month = ImportLog.objects.latest_in_category('prescribing').current_at
    three_months_ago = (
        this_month - relativedelta(months=1)).strftime('%Y-%m-01')
    m = Measure.objects.get(pk=measure)
    if m.numerator_can_be_queried():
        # Awkwardly, because the column names in the prescriptions table
        # are different from those in bigquery (for which the measure
        # definitions are defined), we have to rename them (e.g. `items` ->
        # `total_items`)
        numerator_selector = m.columns_for_select('numerator').replace(
            'items', 'total_items')
        numerator_where = m.numerator_where.replace(
            'bnf_code', 'presentation_code'
        ).replace(
            'bnf_name', 'pn.name'
        ).replace(
            # This is required because the SQL contains %(var)s, which is used
            # for parameter interpolation
            '%', '%%'
        )

        # The redundancy in the following column names is so we can
        # support various flavours of `WHERE` clause from the measure
        # definitions that may use a subset of any of these column
        # names
        query = '''
            WITH nice_names AS (
            SELECT
              bnf_code,
              MAX(name) AS name
            FROM
              dmd_product
            GROUP BY
              bnf_code
            HAVING
              COUNT(*) = 1)
            SELECT
              {org_selector} AS entity,
              presentation_code AS bnf_code,
              COALESCE(nice_names.name, pn.name) AS presentation_name,
              SUM(total_items) AS total_items,
              SUM(actual_cost) AS cost,
              SUM(quantity) AS quantity,
              {numerator_selector}
            FROM
              frontend_prescription p
            LEFT JOIN
              nice_names
            ON p.presentation_code = nice_names.bnf_code
            INNER JOIN
              frontend_presentation pn
            ON p.presentation_code = pn.bnf_code
            WHERE
              {org_selector} = %(org)s
              AND
              processing_date >= %(three_months_ago)s
              AND ({numerator_where})
            GROUP BY
              {org_selector}, presentation_code, nice_names.name, pn.name
            ORDER BY numerator DESC
            LIMIT 50
        '''.format(
             org_selector=org_selector,
             numerator_selector=numerator_selector,
             three_months_ago=three_months_ago,
             numerator_where=numerator_where,
        )
        params = {
            'org': org,
            'three_months_ago': three_months_ago,
        }
        data = utils.execute_query(query, params)
    else:
        data = []
    response = Response(data)
    filename = "%s-%s-breakdown.csv" % (measure, org)
    if request.accepted_renderer.format == 'csv':
        response['content-disposition'] = "attachment; filename=%s" % filename
    return response


@api_view(['GET'])
def measure_by_ccg(request, format=None):
    measure = request.query_params.get('measure', None)
    orgs = utils.param_to_list(request.query_params.get('org', []))
    tags = [x for x in request.query_params.get('tags', '').split(',') if x]
    params = []
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
            params.append(org)
            if (i != len(orgs) - 1):
                query += ' OR '
        query += ") AND "
    query += 'mv.practice_id IS NULL '
    if measure:
        query += "AND mv.measure_id=%s "
        params.append(measure)
    for tag in tags:
        query += "AND %s = ANY(ms.tags) "
        params.append(tag)
    query += "ORDER BY mv.pct_id, measure_id, date"
    data = utils.execute_query(query, [params])
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
    tags = [x for x in request.query_params.get('tags', '').split(',') if x]
    params = []
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
        params.append(org)
    if measure:
        query += "AND mv.measure_id=%s "
        params.append(measure)
    for tag in tags:
        query += "AND %s = ANY(ms.tags) "
        params.append(tag)
    query += "ORDER BY mv.practice_id, measure_id, date"
    data = utils.execute_query(query, [params])
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
