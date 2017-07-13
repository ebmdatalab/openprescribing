from collections import OrderedDict
from sets import Set
import datetime
import re

import numpy as np
import pandas as pd

from django.db import connection
from django.db.models import Q
from django.forms.models import model_to_dict
from django.shortcuts import get_object_or_404

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.exceptions import APIException

from common.utils import namedtuplefetchall
from frontend.models import GenericCodeMapping
from frontend.models import ImportLog
from frontend.models import PPUSaving
from frontend.models import Presentation
import view_utils as utils
from view_utils import db_timeout


class NotValid(APIException):
    status_code = 400
    default_detail = 'The code you provided is not valid'


def _valid_or_latest_date(date):
    if date:
        try:
            date = datetime.datetime.strptime(date, '%Y-%m-%d')
        except ValueError:
            raise NotValid("%s is not a valid date" % date)
    else:
        date = ImportLog.objects.latest_in_category('prescribing').current_at
    return date


def _build_conditions_and_patterns(code, focus):
    if not re.match(r'[A-Z0-9]{15}', code):
        raise NotValid("%s is not a valid code" % code)
    extra_codes = GenericCodeMapping.objects.filter(
        Q(from_code=code) | Q(to_code=code))
    # flatten and uniquify the list of codes
    extra_codes = Set(np.array(
        [[x.from_code, x.to_code] for x in extra_codes]).flatten())
    patterns = ["%s____%s" % (code[:9], code[13:15])]
    for extra_code in extra_codes:
        if extra_code.endswith('%'):
            pattern = extra_code
        else:
            pattern = "%s____%s" % (extra_code[:9], extra_code[13:15])
        patterns.append(pattern)
    conditions = " OR ".join(["presentation_code LIKE %s "] * len(patterns))
    conditions = "AND (%s) " % conditions
    if focus:
        conditions += "AND pct_id = %s "
        patterns.append(focus)
    return conditions, patterns


@api_view(['GET'])
def bubble(request, format=None):
    code = request.query_params.get('bnf_code', '')
    date = _valid_or_latest_date(request.query_params.get('date', None))
    highlight = request.query_params.get('highlight', None)
    focus = request.query_params.get('focus', None) and highlight
    conditions, patterns = _build_conditions_and_patterns(code, focus)
    rounded_ppus_cte_sql = (
        "WITH rounded_ppus AS (SELECT presentation_code, "
        "COALESCE(frontend_presentation.name, 'XXX') as presentation_name, "
        "quantity, practice_id, pct_id, "
        "ROUND(CAST(net_cost/NULLIF(quantity, 0) AS numeric), 2) AS ppu "
        "FROM frontend_prescription "
        "LEFT JOIN frontend_presentation "
        "ON frontend_prescription.presentation_code = "
        "frontend_presentation.bnf_code "
        "LEFT JOIN frontend_practice ON frontend_practice.code = practice_id "
        "WHERE processing_date = %s "
        "AND setting = 4 "
        + conditions +
        ") "
    )
    binned_ppus_sql = rounded_ppus_cte_sql + (
        ", binned_ppus AS (SELECT presentation_code, presentation_name, ppu, "
        "SUM(quantity) AS quantity "
        "FROM rounded_ppus "
        "GROUP BY presentation_code, presentation_name, ppu) "
    )
    ordered_ppus_sql = binned_ppus_sql + (
        "SELECT *, AVG(ppu) OVER (PARTITION BY presentation_code) "
        "AS mean_ppu from binned_ppus "
        "ORDER BY mean_ppu, presentation_name"
    )
    mean_ppu_for_entity_sql = rounded_ppus_cte_sql + (
        "SELECT AVG(ppu) FROM rounded_ppus "
    )
    params = [date] + patterns
    with connection.cursor() as cursor:
        cursor.execute(ordered_ppus_sql, params)
        series = []
        categories = []
        pos = 0
        for result in namedtuplefetchall(cursor):
            if result.presentation_name not in categories:
                categories.append(result.presentation_name)
                pos += 1
            series.append({
                'x': pos,
                'y': result.ppu,
                'z': result.quantity,
                'mean_ppu': result.mean_ppu,
                'name': result.presentation_name})
        categories = list(OrderedDict.fromkeys([x['name'] for x in series]))
        if highlight:
            params.append(highlight)
            if len(highlight) == 3:
                mean_ppu_for_entity_sql += "WHERE pct_id = %s "
            else:
                mean_ppu_for_entity_sql += "WHERE practice_id = %s "
        cursor.execute(mean_ppu_for_entity_sql, params)
        plotline = cursor.fetchone()[0]
        return Response(
            {'plotline': plotline, 'series': series, 'categories': categories})


@api_view(['GET'])
def ppu_histogram(request, format=None):
    code = request.query_params.get('bnf_code', '')
    date = _valid_or_latest_date(request.query_params.get('date', None))
    highlight = request.query_params.get('highlight', None)
    focus = request.query_params.get('focus', None)
    trim = request.query_params.get('trim', None)
    conditions, patterns = _build_conditions_and_patterns(code)
    sql = (
        "SELECT presentation_code, "
        "frontend_presentation.name as presentation_name, "
        "quantity, net_cost, pct_id, practice_id "
        "FROM frontend_prescription "
        "LEFT JOIN frontend_presentation "
        "ON frontend_prescription.presentation_code = "
        "frontend_presentation.bnf_code "
        "LEFT JOIN frontend_practice ON frontend_practice.code = practice_id "
        "WHERE processing_date = %s AND setting = 4 " + conditions +
        "ORDER BY presentation_code, quantity DESC"
    )
    params = [date] + patterns
    df = pd.read_sql(sql, connection, params=params)
    # apparent coding errors lead to absurdly expensive drugs, and
    # these outliers make the charts hard to read, so we remove them
    df['ppu'] = df['net_cost'] / df['quantity']
    if trim:
        df = df[df.ppu <= df.ppu.quantile(0.99)]
    if len(df):
        ordered = df.groupby(
            'presentation_name')['ppu'].aggregate(
                {'mean_ppu': 'mean'}).sort_values(
                    'mean_ppu').index

        # Get plotline for specified entity
        if highlight:
            if len(highlight) == 3:
                mean_ppu = df[df.pct_id == highlight].mean().ppu
            else:
                mean_ppu = df[df.practice_id == highlight].mean().ppu
        else:
            mean_ppu = None
        if mean_ppu is not None and np.isnan(mean_ppu):
            mean_ppu = None
        series = []
        # Compute limits for entire dataset so all histograms use the same
        # scale
        hist, bins = np.histogram(df.ppu)
        # Find a number of bins whereby the bin sizes aren't too close
        # together
        bin_count = len(bins)
        while bin_count > 1 and (bins[1] - bins[0]) < 0.01:
            bin_count = bin_count / 2
            hist, bins = np.histogram(df.ppu, bins=bin_count)
        # Reduce the set we display to individual CCG/Practice, if
        # requested to do so
        if focus:
            if len(highlight) == 3:
                df = df[df.pct_id == highlight]
            else:
                df = df[df.practice_id == highlight]
        # Generate histogram for each presentation
        for name in ordered:
            current = df[df.presentation_name == name]
            # values, bin edges
            current_histogram = np.histogram(
                current.ppu,
                bins=bin_count,
                range=(max(bins[0], 0), bins[-1])
            )
            if (len(current) and
                    current.iloc[0].presentation_code[9:11] == 'AA'):
                is_generic = True
            else:
                is_generic = False

            series.append(
                {'name': name,
                 'is_generic': is_generic,
                 'data': current_histogram[0]})
        series = sorted(series, key=lambda x: x['is_generic'])
        categories = current_histogram[1]
        plotline = mean_ppu
        if plotline:
            # convert it to a ratio that will work with the categories
            plotline = ((plotline - bins[0]) / bins[-1] * len(bins))
        return Response({'mean_ppu': mean_ppu,
                         'plotline': plotline,
                         'categories': categories,
                         'series': series})
    else:
        return Response({'plotline': None, 'series': []})


@api_view(['GET'])
def price_per_unit(request, format=None):
    entity_code = request.query_params.get('entity_code', None)
    date = request.query_params.get('date')
    bnf_code = request.query_params.get('bnf_code', None)
    if not date:
        raise NotValid("You must supply a date")
    if not (entity_code or bnf_code):
        raise NotValid("You must supply a value for entity_code or bnf_code")

    query = {'date': date}
    filename = date
    if entity_code:
        filename += "-%s" % entity_code
        if len(entity_code) == 3:
            # CCG focus
            query['pct'] = entity_code
            if bnf_code:
                # All-practices-for-code-for-one-ccg
                presentation = get_object_or_404(Presentation, pk=bnf_code)
                query['practice__isnull'] = False
                query['presentation'] = presentation
                filename += "-%s" % bnf_code
            else:
                query['practice__isnull'] = True
        else:
            # Practice focus
            query['practice'] = entity_code
    savings = []
    for x in PPUSaving.objects.filter(
            **query).prefetch_related('presentation', 'practice'):
        d = model_to_dict(x)
        try:
            d['name'] = x.presentation.product_name
            d['flag_bioequivalence'] = getattr(
                x.presentation.dmd_product, 'is_non_bioequivalent', None)
        except Presentation.DoesNotExist:
            d['name'] = x.presentation_id
            d['flag_bioequivalence'] = None
        if x.practice:
            d['practice_name'] = x.practice.cased_name
        savings.append(d)
    response = Response(savings)
    if request.accepted_renderer.format == 'csv':
        filename = "%s-ppd.csv" % (filename)
        response['content-disposition'] = "attachment; filename=%s" % filename
    return response


@db_timeout(58000)
@api_view(['GET'])
def total_spending(request, format=None):
    codes = utils.param_to_list(request.query_params.get('code', []))
    codes = utils.get_bnf_codes_from_number_str(codes)

    spending_type = utils.get_spending_type(codes)
    if spending_type is False:
        err = ('Error: BNF Codes must all be the same length if written in '
               'the same search box. For example, you cannot search for '
               'Cerazette_Tab 75mcg (0703021Q0BBAAAA) and Cerelle '
               '(0703021Q0BD), but you could search for Cerazette '
               '(0703021Q0BB) and Cerelle (0703021Q0BD). If you need this '
               'data, please <a href="mailto:{{ SUPPORT_EMAIL }}" '
               'class="doorbell-show">get in touch</a> and we may be able to '
               'extract it for you')
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
        err = ('Error: BNF Codes must all be the same length if written in '
               'the same search box. For example, you cannot search for '
               'Cerazette_Tab 75mcg (0703021Q0BBAAAA) and Cerelle '
               '(0703021Q0BD), but you could search for Cerazette '
               '(0703021Q0BB) and Cerelle (0703021Q0BD). If you need this '
               'data, please <a href="mailto:{{ SUPPORT_EMAIL }}" '
               'class="doorbell-show">get in touch</a> '
               'and we may be able to extract it for you')
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
        err = 'Error: Codes must all be the same length'
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
