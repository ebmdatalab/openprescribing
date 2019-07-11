import re

from dateutil.relativedelta import relativedelta

from rest_framework.decorators import api_view
from rest_framework.exceptions import APIException
from rest_framework.response import Response

from frontend.measure_tags import MEASURE_TAGS
from frontend.models import ImportLog
from frontend.models import Measure
from frontend.models import MeasureGlobal
from frontend.models import MeasureValue

import view_utils as utils


class MissingParameter(APIException):
    status_code = 400
    default_detail = 'You are missing a required parameter.'


class InvalidMultiParameter(APIException):
    status_code = 400
    default_detail = ('You can specify one org and many measures, '
                      'or one measure and many orgs, but not many of both')


@api_view(['GET'])
def measure_global(request, format=None):
    measures = utils.param_to_list(request.query_params.get('measure', None))
    tags = utils.param_to_list(request.query_params.get('tags', None))
    qs = MeasureGlobal.objects.select_related('measure')
    if measures:
        qs = qs.filter(measure_id__in=measures)
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
                'numerator_is_list_of_bnf_codes': measure.numerator_is_list_of_bnf_codes,
                'tags': _hydrate_tags(measure.tags),
                'data': [d_copy]
            }
    d = {
        'measures': [rolled[k] for k in rolled]
    }

    return Response(d)


def _get_org_id_and_type_from_request(request):
    """Return an (org_id, org_type) tuple from the request, normalised
    for various backward-compatibilities.

    Returns (None, None) if no org is specified in the request.

    """
    org_id = utils.param_to_list(request.query_params.get('org', []))
    org_id = org_id and org_id[0]
    org_type = None
    if 'org_type' in request.query_params:
        org_type = request.query_params['org_type'] + '_id'
        if org_type in ['pct_id', 'ccg_id']:
            org_type = 'pr.ccg_id'
    elif org_id:
        # This is here for backwards compatibility, in case anybody else is
        # using the API.  Now we have measures for regional teams, we cannot
        # guess the type of an org by the length of its code, as both CCGs and
        # regional teams have codes of length 3.
        if len(org_id) == 3:
            org_type = 'pr.ccg_id'
        elif len(org_id) == 6:
            org_type = 'practice_id'
        else:
            assert False, 'Unexpected org: {}'.format(org_id)
    return (org_id, org_type)


@api_view(['GET'])
def measure_numerators_by_org(request, format=None):
    measure = request.query_params.get('measure', None)
    org_id, org_type = _get_org_id_and_type_from_request(request)
    this_month = ImportLog.objects.latest_in_category('prescribing').current_at
    three_months_ago = (
        this_month - relativedelta(months=2)).strftime('%Y-%m-01')
    m = Measure.objects.get(pk=measure)
    if m.numerator_is_list_of_bnf_codes:
        if org_type in ['stp_id', 'regional_team_id']:
            extra_join = '''
            INNER JOIN frontend_practice pr
            ON p.practice_id = pr.code
            INNER JOIN frontend_pct
            ON frontend_pct.code = pr.ccg_id
            '''
        elif org_type == 'pr.ccg_id':
            extra_join = '''
            INNER JOIN frontend_practice pr
            ON p.practice_id = pr.code
            '''
        else:
            extra_join = ''

        # For measures whose numerator sums one of the columns in the
        # prescribing table, we order the presentations by that column.
        # For other measures, the columns used to calculate the numerator is
        # not available here (it's in BQ) so we order by total_items, which is
        # the best we can do.
        #
        # But because the columns in BQ don't match the columns in PG (items vs
        # total_items), and because we alias a column in the query below
        # (actual_cost vs cost) we need to translate the name of the column we
        # use for ordering the results.
        match = re.match(
            'SUM\((items|quantity|actual_cost)\) AS numerator',
            m.numerator_columns
        )

        if match:
            order_col = {
                'items': 'total_items',
                'actual_cost': 'cost',
                'quantity': 'quantity',
            }[match.groups()[0]]
        else:
            order_col = 'total_items'

        # The redundancy in the following column names is so we can
        # support various flavours of `WHERE` clause from the measure
        # definitions that may use a subset of any of these column
        # names
        focus_on_org = org_id and org_type
        params = {
            "numerator_bnf_codes": m.numerator_bnf_codes,
            "three_months_ago": three_months_ago,
        }
        if focus_on_org:
            org_condition = "{org_type} = %(org_id)s AND ".format(
                org_type=org_type)
            org_group = "{org_type}, ".format(
                org_type=org_type)
            params["org_id"] = org_id
        else:
            org_condition = ""
            org_group = ""
        query = """
            SELECT
              presentation_code AS bnf_code,
              pn.name AS presentation_name,
              SUM(total_items) AS total_items,
              SUM(actual_cost) AS cost,
              SUM(quantity) AS quantity
            FROM
              frontend_prescription p
            INNER JOIN
              frontend_presentation pn
            ON p.presentation_code = pn.bnf_code
            {extra_join}
            WHERE
              {org_condition}
              processing_date >= %(three_months_ago)s
              AND
              pn.bnf_code = ANY(%(numerator_bnf_codes)s)
            GROUP BY
              {org_group}
              presentation_code, pn.name
            ORDER BY {order_col} DESC
            LIMIT 50
        """.format(
            org_condition=org_condition,
            org_group=org_group,
            org_type=org_type,
            three_months_ago=three_months_ago,
            extra_join=extra_join,
            order_col=order_col,
        )
        data = utils.execute_query(query, params)
    else:
        data = []
    response = Response(data)
    filename = "%s-%s-breakdown.csv" % (measure, org_id)
    if request.accepted_renderer.format == 'csv':
        response['content-disposition'] = "attachment; filename=%s" % filename
    return response


@api_view(['GET'])
def measure_by_regional_team(request, format=None):
    return _measure_by_org(request, 'regional_team')


@api_view(['GET'])
def measure_by_stp(request, format=None):
    return _measure_by_org(request, 'stp')


@api_view(['GET'])
def measure_by_ccg(request, format=None):
    return _measure_by_org(request, 'ccg')


@api_view(['GET'])
def measure_by_practice(request, format=None):
    return _measure_by_org(request, 'practice')


def _measure_by_org(request, org_type):
    measure_ids = utils.param_to_list(request.query_params.get('measure', None))
    tags = utils.param_to_list(request.query_params.get('tags', []))
    org_ids = utils.param_to_list(request.query_params.get('org', []))
    parent_org_type = request.query_params.get('parent_org_type', None)
    aggregate = bool(request.query_params.get('aggregate'))

    if org_type == 'practice' and not (org_ids or aggregate):
        raise MissingParameter
    if len(org_ids) > 1 and len(measure_ids) > 1:
        raise InvalidMultiParameter

    if parent_org_type is None:
        if org_type == 'practice' and org_ids:
            l = len(org_ids[0])
            assert all(len(org_id) == l for org_id in org_ids)

            if l == 3:
                parent_org_type = 'pct'
            elif l == 6:
                parent_org_type = 'practice'
            else:
                assert False, l
        else:
            parent_org_type = org_type

    measure_values = MeasureValue.objects.by_org(
        org_type,
        parent_org_type,
        org_ids,
        measure_ids,
        tags,
    )

    # Because we access the `name` of the related org for each MeasureValue
    # during the roll-up process below we need to prefetch them to avoid doing
    # N+1 db queries
    org_field = org_type if org_type != 'ccg' else 'pct'
    measure_values = measure_values.prefetch_related(org_field)

    if aggregate:
        measure_values = measure_values.aggregate_by_measure_and_month()

    rsp_data = {
        'measures': _roll_up_measure_values(measure_values, org_type)
    }
    return Response(rsp_data)


def _roll_up_measure_values(measure_values, org_type):
    rolled = {}

    for measure_value in measure_values:
        measure_id = measure_value.measure_id
        measure_value_data = {
            'date': measure_value.month,
            'numerator': measure_value.numerator,
            'denominator': measure_value.denominator,
            'calc_value': measure_value.calc_value,
            'percentile': measure_value.percentile,
            'cost_savings': measure_value.cost_savings,
        }

        if org_type == 'practice':
            if measure_value.practice_id:
                measure_value_data.update({
                    'practice_id': measure_value.practice_id,
                    'practice_name': measure_value.practice.name,
                })
        elif org_type == 'ccg':
            if measure_value.pct_id:
                measure_value_data.update({
                    'pct_id': measure_value.pct_id,
                    'pct_name': measure_value.pct.name,
                })
        elif org_type == 'stp':
            if measure_value.stp_id:
                measure_value_data.update({
                    'stp_id': measure_value.stp_id,
                    'stp_name': measure_value.stp.name,
                })
        elif org_type == 'regional_team':
            if measure_value.regional_team_id:
                measure_value_data.update({
                    'regional_team_id': measure_value.regional_team_id,
                    'regional_team_name': measure_value.regional_team.name,
                })
        else:
            assert False

        if measure_id in rolled:
            rolled[measure_id]['data'].append(measure_value_data)
        else:
            measure = measure_value.measure
            rolled[measure_id] = {
                'id': measure_id,
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
                'tags': _hydrate_tags(measure.tags),
                'data': [measure_value_data],
            }

    return rolled.values()


def _hydrate_tags(tag_ids):
    return [
        {'id': tag_id, 'name': MEASURE_TAGS[tag_id]['name']}
        for tag_id in tag_ids
    ]
