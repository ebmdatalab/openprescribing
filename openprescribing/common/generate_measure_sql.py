import csv

reader = csv.DictReader(open('statins.csv', 'rU'))
high_cost_codes = []
all_codes = []
for row in reader:
    if row['HighCost'] == '1':
        high_cost_codes.append(row['BNFcode'])
    all_codes.append(row['BNFcode'])

code_list = "', '".join(high_cost_codes)
str = '"SELECT SUM(total_items) AS items, ",\n'
str += '"SUM(actual_cost) AS cost, ",\n'
str += '"SUM(quantity) AS quantity, ",\n'
str += '"SUM(quantity) AS numerator ",\n'
str += '"FROM frontend_prescription ",\n'
str += '"WHERE (presentation_code IN (\'%s\')) ",\n' % code_list
str += '"AND (practice_id=%s) ",\n'
str += '"AND (processing_date=%s) "'
print str
