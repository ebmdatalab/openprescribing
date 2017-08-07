from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.exceptions import APIException
from django.db.utils import ProgrammingError
import view_utils as utils

STATS_COLUMN_WHITELIST = (
    'total_list_size',
    'astro_pu_items',
    'astro_pu_cost'
)


class KeysNotValid(APIException):
    status_code = 400
    default_detail = 'The keys you provided are not supported'


@api_view(['GET'])
def org_details(request, format=None):
    '''
    Get list size and ASTRO-PU by month, for CCGs or practices.
    '''
    org_type = request.GET.get('org_type', None)
    keys = utils.param_to_list(request.query_params.get('keys', []))
    orgs = utils.param_to_list(request.query_params.get('org', []))
    cols = []

    if org_type == 'practice':
        cols, query = _construct_cols(keys, True)
        query += " FROM frontend_practicestatistics pr "
        query += "JOIN frontend_practice pc ON pr.practice_id=pc.code "
        if orgs:
            query += "WHERE "
            for i, c in enumerate(orgs):
                if len(c) == 3:
                    query += 'pc.ccg_id=%s '
                else:
                    query += "pr.practice_id=%s "
                if (i != len(orgs) - 1):
                    query += ' OR '
        query += "ORDER BY date, row_id"
    elif org_type == 'ccg':
        cols, query = _construct_cols(keys, False)
        query += ' FROM vw__ccgstatistics '
        if orgs:
            query += "WHERE ("
            for i, c in enumerate(orgs):
                query += "pct_id=%s "
                if (i != len(orgs) - 1):
                    query += ' OR '
            query += ') '
        query += 'ORDER BY date'
    else:
        # Total across NHS England.
        json_query, cols = _query_and_cols_for(keys, json_builder_only=True)
        query = 'SELECT date, '
        query += 'AVG(total_list_size) AS total_list_size, '
        query += 'AVG(astro_pu_items) AS astro_pu_items, '
        query += 'AVG(astro_pu_cost) AS astro_pu_cost, '
        query += 'json_object_agg(key, val) AS star_pu '
        query += 'FROM ('
        query += 'SELECT date, '
        query += 'SUM(total_list_size) AS total_list_size, '
        query += 'SUM(astro_pu_items) AS astro_pu_items, '
        query += 'SUM(astro_pu_cost) AS astro_pu_cost, '
        query += 'key, SUM(value::numeric) val '
        query += "FROM vw__ccgstatistics p, json_each_text("
        if json_query:
            query += json_query
        else:
            query += 'star_pu'
        query += ") "
        query += 'GROUP BY date, key '
        query += ') p '
        query += 'GROUP BY date ORDER BY date'
    try:
        if cols:
            data = utils.execute_query(query, [cols, orgs])
        else:
            data = utils.execute_query(query, [orgs])
    except ProgrammingError as e:
        error = str(e)
        if keys and 'does not exist' in error:
            error = error.split('\n')[0].replace('column', 'key')
            raise KeysNotValid(error)
        else:
            raise
    return Response(data)


def _construct_cols(keys, is_practice):
    cols = []
    if is_practice:
        query = "SELECT practice_id AS row_id, name as row_name, date, "
    else:
        query = "SELECT pct_id AS row_id, name as row_name, date, "
    if keys:
        q, cols = _query_and_cols_for(keys)
        query += q
    else:
        query += '* '
    return cols, query


def _query_and_cols_for(keys, json_builder_only=False):
    query = ""
    cols = []
    json_object_keys = []
    for k in keys:
        if k.startswith('star_pu.'):
            star_pu_type = k[len('star_pu.'):]
            json_object_keys.append(star_pu_type)
            cols += [star_pu_type, star_pu_type]
        elif not json_builder_only:
            if k not in STATS_COLUMN_WHITELIST:
                raise KeysNotValid("%s is not a valid key" % k)
            else:
                query += '%s, ' % k
    if json_object_keys:
        query += 'json_build_object('
        for k in json_object_keys:
            query += "%s, star_pu->>%s"
        query += ') '
        if not json_builder_only:
            query += 'AS star_pu'
    if query.endswith(", "):
        query = query[:-2]
    return query, cols
