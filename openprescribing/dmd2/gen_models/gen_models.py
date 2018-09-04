import csv


def model_name(table_name):
    if table_name in [
        'vtm',
        'vpi',
        'vmp',
        'vmpp',
        'amp',
        'ampp',
    ]:
        return table_name.upper()
    else:
        return ''.join(tok.title() for tok in table_name.split('_'))


def quote(s):
    assert '"' not in s
    return '"' + s + '"'


with open('schema.csv') as f:
    lines = list(csv.DictReader(f))


print('from django.db import models')

table = None

for line in lines:
    if line['table'] == 'ccontent':
        continue

    if line['table'] != table:
        table = line['table']
        print()
        print()
        print(f'class {model_name(table)}(models.Model):')

    if line['type'] == 'retired':
        continue

    options = []

    if line['primary_key'] == 'True':
        options.append(('primary_key', 'True'))

    if line['type'] == 'ForeignKey':
        options.append(('to', quote(model_name(line['foreign_key_to']))))
        options.append(('on_delete', 'models.CASCADE'))

        if 'prevcd' in line['field'] or 'uomcd' in line['field']:
            options.append(('related_name', quote('+')))

    elif line['type'] == 'CharField':
        options.append(('max_length', line['max_length']))

    elif line['type'] == 'DecimalField':
        options.append(('max_digits', line['max_digits']))
        options.append(('decimal_places', line['decimal_places']))

    if line['optional'] == 'Y':
        if line['type'] != 'BooleanField' and line['primary_key'] != 'True':
            options.append(('null', 'True'))

    options.append(('help_text', quote(line['descr'])))

    print(f'    {line["field"]} = models.{line["type"]}(')

    for k, v in options:
        print(f'        {k}={v},')
    
    print('    )')
