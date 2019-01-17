from __future__ import print_function

import csv
import json
from collections import OrderedDict


table_names = [
    'vtm',
    'vmp',
    'vmpp',
    'amp',
    'ampp',
]

records = OrderedDict()

with open('schema.csv') as f:
    lines = list(csv.DictReader(f))


table = None

for line in lines:
    if line['table'] == 'ccontent':
        continue

    if line['type'] == 'retired':
        continue

    if line['table'] != table:
        if table is not None:
            records[table] = record

        record = {'dmd_fields': [], 'fields': [], 'dmd_obj_relations': [], 'other_relations': []}
        table = line['table']

    if line['field'] in table_names:
        record['dmd_fields'].append(line['field'])
    else:
        record['fields'].append(line['field'])

    if line['type'] in ['ForeignKey', 'OneToOneField']:
        if line['to'] in table_names:
            if line['table'] in table_names:
                records[line['to']]['dmd_obj_relations'].append(line['table'])
            else:
                records[line['to']]['other_relations'].append(line['table'])

records[table] = record


with open('view-schema.json', 'w') as f:
    json.dump(records, f, indent=4)
