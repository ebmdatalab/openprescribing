import csv
import re

fks = {
    'amppid': 'ampp',
    'apid': 'amp',
    'isid': 'ing',
    'vpid': 'vmp',
    'vppid': 'vmpp',
    'vtmid': 'vtm',
}

with open('schema_raw.csv') as f:
    lines = list(csv.DictReader(f, fieldnames=['table', 'field', 'optional', 'orig_descr']))


last_table = None

for line in lines:
    if line['table'] != last_table:
        last_table = line['table']
        line['primary_key'] = True
        line['type'] = 'IntegerField'

    elif line['field'] in fks:
        line['type'] = 'ForeignKey'
        line['foreign_key_to'] = fks[line['field']]

    elif line['field'] == 'cdprev':
        line['type'] = 'IntegerField'

    elif line['field'][-2:] == 'dt':
        line['type'] = 'DateField'

    elif line['field'] == 'invalid':
        line['type'] = 'BooleanField'

    elif 'narrative' in line['orig_descr'].lower():
        match = re.search('<([\w ]+)>', line['orig_descr'].lower())
        line['type'] = 'ForeignKey'
        line['foreign_key_to'] = match.groups()[0].replace(' ', '')

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
            line['type'] = 'IntegerField'

    elif 'present and set' in line['orig_descr']:
        line['type'] = 'BooleanField'

    elif line['field'] == 'gtin':
        line['type'] = 'IntegerField'

    elif line['field'] == 'dnd':
        line['type'] = 'ForeignKey'
        line['foreign_key_to'] = 'dnd'

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

fieldnames = ['table', 'field', 'optional', 'orig_descr', 'type', 'primary_key', 'foreign_key_to', 'max_length', 'max_digits', 'decimal_places', 'descr']

with open('schema.csv', 'w') as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()

    for line in lines:
        writer.writerow(line)
