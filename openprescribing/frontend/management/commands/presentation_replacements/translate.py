import csv
import glob
import re




files = reversed(sorted(glob.glob("*.txt")))
with open('bnf_codes.csv', 'r') as csvfile:
    codes =  list(csv.reader(csvfile))
    for f in files:
        print "====", f
        for line in open(f, 'r'):
            print "***", line
            prev_code, next_code = line.split("\t")
            prev_code = prev_code.strip()
            next_code = next_code.strip()
            if re.match(r'^[0-9A-Z]+$', next_code):
                matching = [x for x in codes if x[-1].startswith(next_code)]
                for row in matching:
                    new_row = []
                    for field in row:
                        # XXX but also do this for each parent section
                        new_row.append(field.replace(next_code, prev_code))
                    codes.append(new_row)
                    print new_row

            # select everything starting with next_code in that year
            # and generate a list of codes that it would have been in the previous year
            # and write it to a file
            # So we take BNF
