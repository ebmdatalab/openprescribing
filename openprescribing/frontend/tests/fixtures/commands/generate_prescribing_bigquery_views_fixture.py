import csv

practices = [
    ['P87629', '03V'],
    ['K83059', '03V'],
    ['K83622', '03Q'],
    ['N84014', '03Q'],
    ['B82018', '03Q'],
]

presentations = [
    ['0703021P0AAAAAA', 'Norgestrel_Tab 75mcg'],
    ['0703021Q0AAAAAA', 'Desogestrel_Tab 75mcg'],
    ['0703021Q0BBAAAA', 'Cerazette_Tab 75mcg'],
]

f = open('frontend/tests/fixtures/commands/prescribing_bigquery_views_fixture.csv', 'w')
writer = csv.writer(f)

month = '2015-01-01 00:00:00'

for ix, (practice, ccg) in enumerate(practices):
    for jx, (bnf_code, bnf_name) in enumerate(presentations):
        items = 1 + ix + 2 * jx
        quantity = 112 * items
        net_cost = 2.96 * items
        actual_cost = net_cost / 1.06
        
        writer.writerow([
            'Q51',
            ccg,
            practice,
            bnf_code,
            bnf_name,
            items,
            net_cost,
            actual_cost,
            quantity,
            month,
        ])

month = '2015-01-02 00:00:00'

# Practice K83622 moves CCG for 2015_02
assert practices[2][0] == 'K83622'
practices[2][1] = '03V'

for ix, (practice, ccg) in enumerate(practices):
    for jx, (bnf_code, bnf_name) in enumerate(presentations):
        items = 2 + ix + 2 * jx
        quantity = 112 * items
        net_cost = 2.96 * items
        actual_cost = net_cost / 1.06
        
        writer.writerow([
            'Q51',
            ccg,
            practice,
            bnf_code,
            bnf_name,
            items,
            net_cost,
            actual_cost,
            quantity,
            month,
        ])

f.close()
