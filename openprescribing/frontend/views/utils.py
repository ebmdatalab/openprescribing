import csv
from django.http import HttpResponse
from frontend.models import Practice, Section


def convert_get_param_to_list(param_string):
    params = []
    if param_string:
        params = param_string.split(',')
        params = [_f for _f in params if _f]
    return params


def get_practice_ids_from_org(org_string, convert_ccgs_to_practices):
    # Convert CCG codes to lists of practices.
    org_codes = convert_get_param_to_list(org_string)
    practices = []
    for i, org in enumerate(org_codes):
        if convert_ccgs_to_practices and len(org) == 3:
            practices_for_ccg = Practice.objects.filter(ccg_id=org)
            for p in practices_for_ccg:
                practices.append(p.code)
        else:
            practices.append(org)
    return practices


def get_bnf_codes_from_number_str(bnf_string):
    # Convert BNF strings (3.4, 3) to BNF codes (0304, 03).
    code_params = convert_get_param_to_list(bnf_string)
    codes = []
    for code in code_params:
        if '.' in code:
            section = Section.objects.get(number_str=code)
            codes.append(section.bnf_id)
        elif len(code) < 3:
            section = Section.objects.get(bnf_chapter=code, bnf_section=None)
            codes.append(section.bnf_id)
        else:
            codes.append(code)
    return codes


def check_code_params_are_same_type(code_params):
    # Check type of codes, and check that chemical/presentation
    # codes are all the same length, otherwise return error.
    code_len = len(code_params[0])
    if code_len == 9:
        for c in code_params:
            if len(c) != code_len:
                return False
        return 'chemical'
    elif code_len == 11:
        for c in code_params:
            if len(c) != code_len:
                return False
        return 'product'
    elif code_len == 15:
        for c in code_params:
            if len(c) != code_len:
                return False
        return 'presentation'
    elif code_len < 9:
        for c in code_params:
            if len(c) >= 9:
                return False
        return 'bnf-section'
    else:
        return False


def write_csv_response(cursor, filename):
    '''
    Writes a cursor to a CSV file.
    NB: Use StreamingHTTPResponse instead to handle big files?
    https://docs.djangoproject.com/en/1.7/howto/outputting-csv/
    '''
    response = HttpResponse(content_type='text/csv')
    csv_name = "%s.csv" % filename  # TODO: Include date here
    response['Content-Disposition'] = 'attachment; filename="%s"' % csv_name
    writer = csv.writer(response)
    cursor_copy = []
    for c in cursor:
        c = [str(item).encode('utf8') for item in c]
        cursor_copy.append(c)
    writer.writerow([str(i[0]).encode('utf8') for i in cursor.description])
    writer.writerows(cursor_copy)
    return response
