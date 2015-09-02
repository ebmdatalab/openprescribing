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
        orgs = utils.get_practice_ids_from_org(orgs)
        query = "SELECT pr.date as date, pr.practice_id as row_id, "
        query += "pc.name as row_name, "
        query += "pr.total_list_size, pr.astro_pu_cost, "
        query += "pr.astro_pu_items, pr.star_pu_oral_antibac_items "
        query += "FROM frontend_practicelist pr "
        query += "JOIN frontend_practice pc ON pr.practice_id=pc.code "
        if orgs:
            query += "WHERE "
            for i, c in enumerate(orgs):
                query += "pr.practice_id=%s "
                if (i != len(orgs)-1):
                    query += ' OR '
            query += "ORDER BY date, row_id"
        else:
            query += "ORDER BY date, row_id"
    elif org_type == 'ccg':
        query = "SELECT pr.date, pr.pct_id as row_id, "
        query += "pc.name as row_name, "
        query += "SUM(pr.total_list_size) AS total_list_size, "
        query += "SUM(pr.astro_pu_cost) AS astro_pu_cost, "
        query += "SUM(pr.astro_pu_items) AS astro_pu_items, "
        query += "SUM(pr.star_pu_oral_antibac_items) "
        query += "AS star_pu_oral_antibac_items "
        query += "FROM frontend_practicelist pr "
        query += "JOIN frontend_pct pc ON pr.pct_id=pc.code "
        query += "WHERE pc.org_type='CCG' "
        if orgs:
            query += "AND ("
            for i, c in enumerate(orgs):
                query += "pct_id=%s "
                if (i != len(orgs)-1):
                    query += ' OR '
            query += ') '
            query += "GROUP BY pr.pct_id, pc.name, date ORDER BY date, row_id"
        else:
            query += "GROUP BY pr.pct_id, pc.name, date ORDER BY date, row_id"
    else:
        # Total across NHS England.
        query = "SELECT date, SUM(total_list_size) as total_list_size, "
        query += "SUM(astro_pu_cost) AS astro_pu_cost, "
        query += "SUM(astro_pu_items) AS astro_pu_items, "
        query += "SUM(star_pu_oral_antibac_items) "
        query += "AS star_pu_oral_antibac_items "
        query += "FROM frontend_practicelist "
        query += "GROUP BY date ORDER BY date"

    data = utils.execute_query(query, [orgs])
    return Response(data)
