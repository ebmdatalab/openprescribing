from rest_framework.decorators import api_view
from rest_framework.response import Response
import view_utils as utils
from view_utils import db_timeout


CODE_LENGTH_ERROR = (
    'Error: BNF Codes must all be the same length if written in the same '
    'search box. For example, you cannot search for Cerazette_Tab 75mcg '
    '(0703021Q0BBAAAA) and Cerelle (0703021Q0BD), but you could search for '
    'Cerazette (0703021Q0BB) and Cerelle (0703021Q0BD). If you need this '
    'data, please <a href="mailto:{{ SUPPORT_EMAIL }}" '
    'class="doorbell-show">get in touch</a> and we may be able to extract it '
    'for you')


@db_timeout(58000)
@api_view(['GET'])
def total_spending(request, format=None):
    codes = utils.param_to_list(request.query_params.get('code', []))
    codes = utils.get_bnf_codes_from_number_str(codes)

    spending_type = utils.get_spending_type(codes)
    if spending_type is False:
        err = CODE_LENGTH_ERROR
        return Response(err, status=400)

    query = _get_query_for_total_spending(codes)

    if spending_type != 'presentation':
        codes = [c + '%' for c in codes]

    data = utils.execute_query(query, [codes])
    return Response(data)


@db_timeout(58000)
@api_view(['GET'])
def spending_by_ccg(request, format=None):
    codes = utils.param_to_list(request.query_params.get('code', []))
    codes = utils.get_bnf_codes_from_number_str(codes)
    orgs = utils.param_to_list(request.query_params.get('org', []))

    spending_type = utils.get_spending_type(codes)
    if spending_type is False:
        err = CODE_LENGTH_ERROR
        return Response(err, status=400)

    if not spending_type or spending_type == 'bnf-section' \
       or spending_type == 'chemical':
        query = _get_query_for_chemicals_or_sections_by_ccg(codes, orgs,
                                                            spending_type)
    else:
        query = _get_query_for_presentations_by_ccg(codes, orgs)

    if spending_type == 'bnf-section' or spending_type == 'product':
        codes = [c + '%' for c in codes]

    data = utils.execute_query(query, [codes, orgs])
    return Response(data)


@db_timeout(58000)
@api_view(['GET'])
def spending_by_practice(request, format=None):
    codes = utils.param_to_list(request.query_params.get('code', []))
    codes = utils.get_bnf_codes_from_number_str(codes)
    orgs = utils.param_to_list(request.query_params.get('org', []))
    date = request.query_params.get('date', None)

    spending_type = utils.get_spending_type(codes)
    if spending_type is False:
        err = CODE_LENGTH_ERROR
        return Response(err, status=400)
    if spending_type == 'bnf-section' or spending_type == 'product':
        codes = [c + '%' for c in codes]

    if not date and not orgs:
        err = 'Error: You must supply either '
        err += 'a list of practice IDs or a date parameter, e.g. '
        err += 'date=2015-04-01'
        return Response(err, status=400)

    org_for_param = None
    if not spending_type or spending_type == 'bnf-section' \
       or spending_type == 'chemical':
        # We can do presentation queries indexed by PCT ID, which is faster.
        # We have yet to update the *_by_practice matviews with PCT ID.
        # So for these queries, expand the CCG ID to a list of practice IDs.
        expanded_orgs = utils.get_practice_ids_from_org(orgs)
        if codes:
            query = _get_chemicals_or_sections_by_practice(codes,
                                                           expanded_orgs,
                                                           spending_type,
                                                           date)
            org_for_param = expanded_orgs
        else:
            query = _get_total_spending_by_practice(expanded_orgs, date)
            org_for_param = expanded_orgs
    else:
        query = _get_presentations_by_practice(codes, orgs, date)
        org_for_param = orgs
    data = utils.execute_query(
        query, [codes, org_for_param, [date] if date else []])
    return Response(data)


def _get_query_for_total_spending(codes):
    # The CTE at the start ensures we return rows for every month in
    # the last five years, even if that's zeros
    query = """WITH all_dates AS (
                 SELECT
                   MAX(current_at)::date - (d.date||'month')::interval AS date
                 FROM
                   generate_series(0,
                     59) AS d(date),
                   frontend_importlog
                 WHERE
                   category = 'prescribing'
                 GROUP BY
                   category,
                   d.date
                 ORDER BY
                   date)
               SELECT
                 COALESCE(SUM(cost), 0) AS actual_cost,
                 COALESCE(SUM(items), 0) AS items,
                 COALESCE(SUM(quantity), 0) AS quantity,
                 all_dates.date::date AS date
               FROM (
                 SELECT *
                 FROM
                   vw__presentation_summary
                 %s
               ) pr
               RIGHT OUTER JOIN all_dates
               ON all_dates.date = pr.processing_date
               GROUP BY date
               ORDER BY date;"""
    if codes:
        condition = " WHERE ("
        for i, c in enumerate(codes):
            condition += "presentation_code LIKE %s "
            if (i != len(codes) - 1):
                condition += ' OR '
        condition += ") "
    else:
        condition = ""

    return query % condition


def _get_query_for_chemicals_or_sections_by_ccg(codes, orgs, spending_type):
    query = 'SELECT pr.pct_id as row_id, '
    query += "pc.name as row_name, "
    query += 'pr.processing_date as date, '
    query += 'SUM(pr.cost) AS actual_cost, '
    query += 'SUM(pr.items) AS items, '
    query += 'SUM(pr.quantity) AS quantity '
    query += "FROM vw__chemical_summary_by_ccg pr "
    query += "JOIN frontend_pct pc ON pr.pct_id=pc.code "
    query += "AND pc.org_type='CCG' "
    if spending_type:
        query += " WHERE ("
        if spending_type == 'bnf-section':
            for i, c in enumerate(codes):
                query += "pr.chemical_id LIKE %s "
                if (i != len(codes) - 1):
                    query += ' OR '
            codes = [c + '%' for c in codes]
        else:
            for i, c in enumerate(codes):
                query += "pr.chemical_id=%s "
                if (i != len(codes) - 1):
                    query += ' OR '
        query += ") "
    if orgs:
        query += "AND ("
        for i, org in enumerate(orgs):
            query += "pr.pct_id=%s "
            if (i != len(orgs) - 1):
                query += ' OR '
        query += ") "
    query += "GROUP BY pr.pct_id, pc.code, date "
    query += "ORDER BY date, pr.pct_id "
    return query


def _get_query_for_presentations_by_ccg(codes, orgs):
    query = 'SELECT pr.pct_id as row_id, '
    query += "pc.name as row_name, "
    query += 'pr.processing_date as date, '
    query += "SUM(pr.items) AS items, "
    query += 'SUM(pr.cost) AS actual_cost, '
    query += 'SUM(pr.quantity) AS quantity '
    query += "FROM vw__presentation_summary_by_ccg pr "
    query += "JOIN frontend_pct pc ON pr.pct_id=pc.code "
    query += "AND pc.org_type='CCG' "
    query += " WHERE ("
    for i, c in enumerate(codes):
        query += "pr.presentation_code LIKE %s "
        if (i != len(codes) - 1):
            query += ' OR '
    if orgs:
        query += ") AND ("
        for i, org in enumerate(orgs):
            query += "pr.pct_id=%s "
            if (i != len(orgs) - 1):
                query += ' OR '
    query += ") GROUP BY pr.pct_id, pc.code, date "
    query += "ORDER BY date, pr.pct_id"
    return query


def _get_total_spending_by_practice(orgs, date):
    query = 'SELECT pr.practice_id AS row_id, '
    query += "pc.name AS row_name, "
    query += "pc.setting AS setting, "
    query += "pc.ccg_id AS ccg, "
    query += 'pr.processing_date AS date, '
    query += 'pr.cost AS actual_cost, '
    query += 'pr.items AS items, '
    query += 'pr.quantity AS quantity '
    query += "FROM vw__practice_summary pr "
    query += "JOIN frontend_practice pc ON pr.practice_id=pc.code "
    if orgs or date:
        query += "WHERE "
    if date:
        query += "pr.processing_date=%s "
    if orgs:
        if date:
            query += "AND "
        query += "("
        for i, org in enumerate(orgs):
            query += "pr.practice_id=%s "
            # if len(org) == 3:
            #     query += "pr.pct_id=%s "
            # else:
            #     query += "pr.practice_id=%s "
            if (i != len(orgs) - 1):
                query += ' OR '
        query += ") "
    query += "ORDER BY date, pr.practice_id "
    return query


def _get_chemicals_or_sections_by_practice(codes, orgs, spending_type,
                                           date):
    query = 'SELECT pr.practice_id AS row_id, '
    query += "pc.name AS row_name, "
    query += "pc.setting AS setting, "
    query += "pc.ccg_id AS ccg, "
    query += "pr.processing_date AS date, "
    query += 'SUM(pr.cost) AS actual_cost, '
    query += 'SUM(pr.items) AS items, '
    query += 'SUM(pr.quantity) AS quantity '
    query += "FROM vw__chemical_summary_by_practice pr "
    query += "JOIN frontend_practice pc ON pr.practice_id=pc.code "
    has_preceding = False
    if spending_type:
        has_preceding = True
        query += " WHERE ("
        if spending_type == 'bnf-section':
            for i, c in enumerate(codes):
                query += "pr.chemical_id LIKE %s "
                if (i != len(codes) - 1):
                    query += ' OR '
            codes = [c + '%' for c in codes]
        else:
            for i, c in enumerate(codes):
                query += "pr.chemical_id=%s "
                if (i != len(codes) - 1):
                    query += ' OR '
        query += ") "
    if orgs:
        if has_preceding:
            query += " AND ("
        else:
            query += " WHERE ("
        for i, org in enumerate(orgs):
            query += "pr.practice_id=%s "
            # if len(org) == 3:
            #     query += "pr.pct_id=%s "
            # else:
            #     query += "pr.practice_id=%s "
            if (i != len(orgs) - 1):
                query += ' OR '
        query += ") "
        has_preceding = True
    if date:
        if has_preceding:
            query += " AND ("
        else:
            query += " WHERE ("
        query += "pr.processing_date=%s) "
    query += "GROUP BY pr.practice_id, pc.code, date "
    query += "ORDER BY date, pr.practice_id"
    return query


def _get_presentations_by_practice(codes, orgs, date):
    query = 'SELECT pr.practice_id AS row_id, '
    query += "pc.name AS row_name, "
    query += "pc.setting AS setting, "
    query += "pc.ccg_id AS ccg, "
    query += "pr.processing_date AS date, "
    query += 'SUM(pr.actual_cost) AS actual_cost, '
    query += 'SUM(pr.total_items) AS items, '
    query += 'CAST(SUM(pr.quantity) AS bigint) AS quantity '
    query += "FROM frontend_prescription pr "
    query += "JOIN frontend_practice pc ON pr.practice_id=pc.code "
    query += "WHERE ("
    for i, c in enumerate(codes):
        query += "pr.presentation_code LIKE %s "
        if (i != len(codes) - 1):
            query += ' OR '
    if orgs:
        query += ") AND ("
        for i, c in enumerate(orgs):
            if len(c) == 3:
                query += "pr.pct_id=%s "
            else:
                query += "pr.practice_id=%s "
            if (i != len(orgs) - 1):
                query += ' OR '
    if date:
        query += "AND pr.processing_date=%s "
    query += ") GROUP BY pr.practice_id, pc.code, date "
    query += "ORDER BY date, pr.practice_id"
    return query
