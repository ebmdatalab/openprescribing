# We generate two CSV files containing practices belonging to 6 CCGs.
#
# In epraccur1.csv, 5 CCGs have 9 practices, of which:
#
# * 6 are active in setting 4
# * 2 are closed with setting 4
# * 1 is active with setting 9
#
# epraccur2.csv introduces a new CCG (C06), and describes various changes to
# the composition of the existing CCGs:
#
# * 3 practices move from C01 to C02
# * C04 closes, with 3 practices moving to C03 and 3 to C06
# * C05 closes, with all pracitces moving to C06
#
# When a CCG's composition changes, only active GP practices (ie, with setting
# 4) are moved.

import csv


def build_row(practice_code, ccg_code, status_code, setting):
    row = ['' for _ in range(27)]
    row[0] = practice_code
    row[1] = 'Practice {} (status: {}, setting: {})'.format(
        practice_code, status_code, setting)
    row[10] = '20170101'  # open_date, expected by import_practices
    row[12] = status_code
    row[23] = ccg_code
    row[25] = setting
    return row


rows = []

for ccg_ix in range(5):
    ccg_code = 'C{:02}'.format(ccg_ix + 1)

    for practice_ix in range(9):
        practice_code = 'A{:05}'.format(ccg_ix * 9 + practice_ix + 1)

        if practice_ix < 6:
            status_code, setting = 'A', 4
        elif practice_ix < 8:
            status_code, setting = 'C', 4
        elif practice_ix < 9:
            status_code, setting = 'A', 9
        else:
            assert False

        rows.append(build_row(practice_code, ccg_code, status_code, setting))


with open('epraccur1.csv', 'w') as f:
    writer = csv.writer(f)
    for row in rows:
        writer.writerow(row)

num_moved_from_C01 = 0
num_moved_from_C04 = 0

for row in rows:
    if row[12] != 'A' or row[25] != 4:
        continue

    if row[23] == 'C01':
        if num_moved_from_C01 < 3:
            # Move 3 active GP practices from C01 to C02
            row[23] = 'C02'
            num_moved_from_C01 += 1

    elif row[23] == 'C04':
        if num_moved_from_C04 < 3:
            # Move 3 active GP practices from C04 to C03
            row[23] = 'C03'
        else:
            # Move 3 active GP practices from C04 to C06
            row[23] = 'C06'
        num_moved_from_C04 += 1

    elif row[23] == 'C05':
        # Move all active GP practices from C05 to C06
        row[23] = 'C06'


with open('epraccur2.csv', 'w') as f:
    writer = csv.writer(f)
    for row in rows:
        writer.writerow(row)
