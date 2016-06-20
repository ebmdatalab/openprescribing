from rest_framework.decorators import api_view
from rest_framework.response import Response
import view_utils as utils


@api_view(['GET'])
def org_details(request, format=None):
    '''
    Get list size and ASTRO-PU by month, for CCGs or practices.
    '''
    org_type = request.GET.get('org_type', None)
    orgs = utils.param_to_list(request.query_params.get('org', []))

    if org_type == 'practice':
        query = "SELECT pr.date as date, pr.practice_id as row_id, "
        query += "pc.name as row_name, "
        query += "pr.total_list_size, pr.astro_pu_cost, "
        query += "pr.astro_pu_items, pr.star_pu "
        query += "FROM frontend_practicestatistics pr "
        query += "JOIN frontend_practice pc ON pr.practice_id=pc.code "
        if orgs:
            query += "WHERE "
            for i, c in enumerate(orgs):
                if len(c) == 3:
                    query += 'pr.pct_id=%s '
                else:
                    query += "pr.practice_id=%s "
                if (i != len(orgs) - 1):
                    query += ' OR '
            query += "ORDER BY date, row_id"
        else:
            query += "ORDER BY date, row_id"
    elif org_type == 'ccg':
        query = 'SELECT pct_id AS row_id, name as row_name, *'
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
        query += 'FROM vw__ccgstatistics p, json_each_text(star_pu) '
        query += 'GROUP BY date, key '
        query += ') p '
        query += 'GROUP BY date ORDER BY date'
    data = utils.execute_query(query, [orgs])
    return Response(data)
