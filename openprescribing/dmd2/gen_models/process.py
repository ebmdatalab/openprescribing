import csv
import re

fks = {
    'amppid': 'ampp',
    'apid': 'amp',
    'appid': 'ampp',
    'isid': 'ing',
    'vpid': 'vmp',
    'vppid': 'vmpp',
    'vtmid': 'vtm',
}


with open('schema_raw.csv') as f:
    lines = list(csv.DictReader(f, fieldnames=['table', 'field', 'optional', 'orig_descr']))


table = None

for line in lines:
    if line['table'] == 'ccontent':
        continue

    if line['table'] != table:
        table = line['table']

        if line['field'] == 'cd' or fks[line['field']] == table:
            line['primary_key'] = True
            if 'maximum of 18' in line['orig_descr']:
                line['type'] = 'BigIntegerField'
            else:
                line['type'] = 'IntegerField'

            if line['field'] != 'cd':
                line['db_column'] = line['field']
                line['field'] = 'id'

        else:
            if line['table'] in [
                'vpi',
                'ont',
                'droute',
                'ap_ing',
                'lic_route',
            ]:
                line['type'] = 'ForeignKey'
            else:
                line['type'] = 'OneToOneField'

            line['to'] = fks[line['field']]
            line['db_column'] = line['field']
            line['field'] = fks[line['field']]

    elif line['field'] in fks:
        line['type'] = 'ForeignKey'
        line['to'] = fks[line['field']]
        line['db_column'] = line['field']
        line['field'] = fks[line['field']]

    elif line['field'] == 'cdprev':
        if 'maximum of 18' in line['orig_descr']:
            line['type'] = 'BigIntegerField'
        else:
            line['type'] = 'IntegerField'

    elif line['field'][-2:] == 'dt':
        line['type'] = 'DateField'

    elif line['field'] == 'invalid':
        line['type'] = 'BooleanField'

    elif 'narrative' in line['orig_descr'].lower():
        assert line['field'][-2:] == 'cd'
        line['type'] = 'ForeignKey'
        match = re.search('<([\w ]+)>', line['orig_descr'].lower())
        line['to'] = match.groups()[0].replace(' ', '')
        line['db_column'] = line['field']
        line['field'] = line['field'][:-2]

    elif 'decimal' in line['orig_descr']:
        line['type'] = 'DecimalField'
        line['max_digits'] = re.search('(\d+) digits', line['orig_descr']).groups()[0]
        line['decimal_places'] = re.search('(\d+) decimal places', line['orig_descr']).groups()[0]

    elif 'maximum' in line['orig_descr']:
        match = re.search('maximum of (\d+) char', line['orig_descr'])
        if match is not None:
            line['type'] = 'CharField'
            line['max_length'] = match.groups()[0]

        else:
            if 'maximum of 18' in line['orig_descr']:
                line['type'] = 'BigIntegerField'
            else:
                line['type'] = 'IntegerField'

    elif 'present and set' in line['orig_descr']:
        line['type'] = 'BooleanField'

    elif line['field'] == 'gtin':
        line['type'] = 'BigIntegerField'

    elif line['field'] == 'dnd':
        line['type'] = 'ForeignKey'
        line['to'] = 'dnd'
        line['db_column'] = 'dndcd'

    elif line['field'] == 'ltd_stab':
        line['type'] = 'retired'

    else:
        print('-' * 80)
        print(line['table'], line['field'])
        print(line['orig_descr'])
        assert False


    if line['field'] == 'cd':
        descr = 'Code'

    elif line['field'] == 'desc':
        line['field'] = 'descr'
        descr = 'Description'

    else:
        descr = line['orig_descr']

        for splitter in [
            '(',
            '-',
            '–',
            'Up to a',
            'narrative',
            'Narrative',
            'Always 10',
            'Either',
            'will be present',
        ]:
            ix = descr.find(' ' + splitter)
            if ix != -1:
                descr = descr[:ix]

        descr = descr.strip()
        descr = descr.split('.')[0]
        descr = descr.split(',')[0]

        descr = descr.replace('Virtual Therapeutic Moiety', 'VTM')
        descr = descr.replace('Virtual Medicinal Product Pack', 'VMPP')
        descr = descr.replace('Virtual medicinal product pack', 'VMPP')
        descr = descr.replace('virtual product pack', 'VMPP')
        descr = descr.replace('Virtual Medicinal Product', 'VMP')
        descr = descr.replace('Actual Medicinal Product Pack', 'AMPP')
        descr = descr.replace('Actual Medicinal Product', 'AMP')
        descr = descr.replace('Actual Product', 'AMP')

    line['descr'] = descr

fieldnames = ['table', 'field', 'optional', 'orig_descr', 'type', 'primary_key', 'db_column', 'to', 'max_length', 'max_digits', 'decimal_places', 'descr']

with open('schema.csv', 'w') as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()

    for line in lines:
        writer.writerow(line)
