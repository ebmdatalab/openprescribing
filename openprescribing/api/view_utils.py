import itertools
from django.db import connection
from frontend.models import Practice, Section


def param_to_list(str):
    params = []
    if str:
        params = str.split(',')
        params = filter(None, params)
    return params


def dictfetchall(cursor):
    desc = cursor.description
    return [
        dict(zip([col[0] for col in desc], row))
        for row in cursor.fetchall()
    ]


def execute_query(query, params):
    cursor = connection.cursor()
    if params:
        cursor.execute(query, tuple(itertools.chain.from_iterable(params)))
    else:
        cursor.execute(query)
    data = dictfetchall(cursor)
    cursor.close()
    return data


def get_practice_ids_from_org(org_codes):
    # Convert CCG codes to lists of practices.
    practices = []
    for i, org in enumerate(org_codes):
        if len(org) == 3:
            practices_for_ccg = Practice.objects.filter(ccg_id=org)
            for p in practices_for_ccg:
                practices.append(p.code)
        else:
            practices.append(org)
    return practices


def get_bnf_codes_from_number_str(codes):
    # Convert BNF strings (3.4, 3) to BNF codes (0304, 03).
    converted = []
    for code in codes:
        if '.' in code:
            section = Section.objects.get(number_str=code)
            converted.append(section.bnf_id)
        elif len(code) < 3:
            section = Section.objects.get(bnf_chapter=code, bnf_section=None)
            converted.append(section.bnf_id)
        else:
            converted.append(code)
    return converted


def get_spending_type(codes):
    # Codes must all be of the same length.
    if not codes:
        return None
    code_len = len(codes[0])
    for c in codes:
        if len(c) != code_len:
            return False
    if code_len < 9:
        return 'bnf-section'
    elif code_len == 9:
        return 'chemical'
    elif code_len > 9 and code_len <= 11:
        return 'product'
    elif code_len > 11:
        return 'presentation'
