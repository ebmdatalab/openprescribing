echo 'Importing BNF codes and chemicals...'
python manage.py import_bnf_codes --filename data/bnf_codes/bnf_codes.csv -v 2
python manage.py import_adqs --filename data/bnf_codes/adqs_april_16.csv -v 2
python manage.py import_hscic_chemicals -v 2

echo 'Fetching and converting HSCIC prescribing data...'
python manage.py fetch_hscic_prescribing -v 2
python manage.py convert_hscic_prescribing -v 2

echo 'Importing organisation details...'
python manage.py import_ccg_boundaries --filename data/org_codes/CCC_Feb2013.KML -v 2
python manage.py import_org_names --ccg data/org_codes/eccg.csv
python manage.py import_practices --filename data/org_codes/epraccur.csv -v 2
python manage.py geocode_practices -v 2 --filename data/gridall.csv

echo 'Importing HSCIC prescribing data'
python manage.py import_hscic_prescribing -v 2

echo 'Importing list sizes...'
python manage.py import_list_sizes -v 2

echo 'Updating database...'
python manage.py create_indexes
python manage.py create_matviews
