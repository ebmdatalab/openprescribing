import csv


def fix_line(line):
    if len(line) == 2:
        line = [line[0], '', line[1]]

    if len(line) > 3:
        line = [line[0], line[1], ' '.join(line[2:])]

    line = [' '.join(item.split()) for item in line]

    if line[2] == '':
        line[1], line[2] = line[2], line[1]

    if line[1] not in ['Y', '']:
        line[1], line[2] = '', ' '.join([line[1], line[2]])

    if line[2] == 'End Tag':
        if line[0][:2] != '</':
            line[0] = '</' + line[0][1:]

    line[0] = line[0].replace(' ', '')

    return line

lines = []
root_tag = None
last_line = None

with open('schema_very_raw.csv') as f:
    raw_lines = list(csv.reader(f))


for line in raw_lines:
    if 'GTINDATA' in line[0]:
        continue

    if root_tag is None:
        if 'Root Node' in line or line[0] == '<ACTUAL_MEDICINAL_PROD_PACKS>':
            root_tag = line[0][1:-1]
            last_line = None
        continue
    elif line[0] == f'</{root_tag}>':
        last_line = fix_line(last_line)

        if last_line[0] not in ['<INFO>', '</INFO>']:
            lines.append(last_line)

        root_tag = None
        last_line = None
        continue

    line = [item.replace('\n', ' ') for item in line]

    if last_line is None:
        last_line = line
    else:
        if line[0] == '':
            for item in line[1:]:
                last_line[-1] += f' {item}'
        else:
            last_line = fix_line(last_line)

            if last_line[0] not in ['<INFO>', '</INFO>']:
                lines.append(last_line)

            last_line = line


pointless_tags = []

for line in lines:
    if line[2] == 'End Tag':
        if end_tag:
            pointless_tags.append(line[0][2:-1])
        else:
            end_tag = True
    else:
        end_tag = False


lines = [
    line for line in lines
    if line[0] not in [f'<{tag}>' for tag in pointless_tags] + [f'</{tag}>' for tag in pointless_tags]
]


lines1 = []
table_name = None

for line in lines:
    if table_name is None:
        table_name = line[0][1:-1].lower()
        continue

    if line[2] == 'End Tag':
        table_name = None
        continue

    lines1.append([table_name, line[0][1:-1].lower(), line[1], line[2]])


change_table_name = False

for line in lines1:
    if line[1] == 'amppid':
        change_table_name = True
        line[1] = 'appid'

    if change_table_name:
        line[0] = 'gtin'


with open('schema_raw.csv', 'w') as f:
    writer = csv.writer(f)

    for line in lines1:
        writer.writerow(line)
