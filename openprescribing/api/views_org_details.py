from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.exceptions import APIException
from django.db.utils import ProgrammingError
import view_utils as utils

CCG_STATS_COLUMN_WHITELIST = (
    'row_id',
    'row_name',
    'date',
    'total_list_size',
    'astro_pu_items',
    'astro_pu_cost',
    'star_pu.lipid-regulating_drugs_cost',
    'star_pu.ulcer_healing_drugs_cost',
    'star_pu.statins_cost',
    'star_pu.proton_pump_inhibitors_cost',
    'star_pu.oral_nsaids_cost',
'star_pu.oral_antibacterials_item',
    'star_pu.oral_antibacterials_cost',
    'star_pu.omega-3_fatty_acid_compounds_adq',
'star_pu.laxatives_cost',
    'star_pu.inhaled_corticosteroids_cost',
    'star_pu.hypnotics_adq',
'star_pu.drugs_used_in_parkinsonism_and_related_disorders_cost',
    'star_pu.drugs_for_dementia_cost',
    'star_pu.drugs_affecting_the_renin_angiotensin_system_cost',
    'star_pu.drugs_acting_on_benzodiazepine_receptors_cost',
'star_pu.cox-2_inhibitors_cost',
    'star_pu.calcium-channel_blockers_cost',
    'star_pu.bronchodilators_cost',
    'star_pu.bisphosphonates_and_other_drugs_cost',
    'star_pu.benzodiazepine_caps_and_tabs_cost',
    'star_pu.antiplatelet_drugs_cost',
    'star_pu.antiepileptic_drugs_cost',
    'star_pu.antidepressants_cost',
    'star_pu.antidepressants_adq',
    'star_pu.analgesics_cost'
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
                if (i != len(orgs)-1):
                    query += ' OR '
            query += "ORDER BY date, row_id"
        else:
            query += "ORDER BY date, row_id"
    elif org_type == 'ccg':
        if keys:
            cols = []
            aliases = {'row_id': 'pct_id',
                       'row_name': 'name'}
            for k in keys:
                if k not in CCG_STATS_COLUMN_WHITELIST:
                    raise KeysNotValid("%s is not a valid key" % k)
                if k.startswith('star_pu.'):
                    star_pu_type = k[len('star_pu.'):]
                    cols.append(
                        "json_build_object('%s', star_pu->>'%s') AS star_pu" %
                        (star_pu_type, star_pu_type)
                    )
                else:
                    if k in aliases:
                        cols.append("%s AS %s" % (aliases[k], k))
                    else:
                        cols.append(k)
            query = "SELECT %s" % ", ".join(cols)
        else:
            query = 'SELECT pct_id AS row_id, name as row_name, *'
        query += ' FROM vw__ccgstatistics '
        if orgs:
            query += "WHERE ("
            for i, c in enumerate(orgs):
                query += "pct_id=%s "
                if (i != len(orgs)-1):
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
    try:
        data = utils.execute_query(query, [orgs])
    except ProgrammingError as e:
        error = str(e)
        if keys and 'does not exist' in error:
            error = error.split('\n')[0].replace('column', 'key')
            raise KeysNotValid(error)
        else:
            raise
    return Response(data)


def _build_org_query(keys, orgs):
    query = ""
    if keys:
        keys = keys.split(",")
        cols = []
        aliases = {'row_id': 'pct_id',
                   'row_name': 'name'}
        for k in keys:
            if k.startswith('star_pu.'):
                star_pu_type = k[len('star_pu.'):]
                cols.append(
                    "json_build_object('%s', star_pu->>'%s') AS star_pu" %
                    (star_pu_type, star_pu_type)
                )
            else:
                if k in aliases:
                    cols.append("%s AS %s" % (aliases[k], k))
                else:
                    cols.append(k)
        query = "SELECT %s" % ", ".join(cols)
    else:
        query = 'SELECT pct_id AS row_id, name as row_name, *'
    query += ' FROM vw__ccgstatistics '

    # select json_build_object('asd', star_pu->>'analgesics_cost') as star_pu from vw__ccgstatistics limit 1;
    if orgs:
        query += "WHERE ("
        for i, c in enumerate(orgs):
            query += "pct_id=%s "
            if (i != len(orgs)-1):
                query += ' OR '
        query += ') '
    query += 'ORDER BY date'
    return query
