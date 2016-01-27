echo 'Fetching HSCIC data...'
python manage.py fetch_hscic_prescribing

echo 'Converting HSCIC data...'
python manage.py convert_hscic_prescribing

echo 'Importing HSCIC practices...'
python manage.py import_hscic_practices

echo 'Geocoding HSCIC practices...'
python manage.py geocode_practices -v 2

echo 'Importing HSCIC prescribing data...'
python manage.py import_hscic_prescribing

echo 'Importing other data...'
# This section is out of date!
python manage.py import_list_sizes
python manage.py import_org_names
python manage.py import_practice_prescribing_status --filename data/org_codes/epraccur.csv -v 2
python manage.py import_practice_to_ccg_relations
python manage.py import_qof_prevalence
python manage.py import_bnf_codes --filename data/bnf_codes/bnf_codes.csv -v 2
python manage.py import_ccg_boundaries --filename data/org_codes/CCC_Feb2013.KML -v 2

echo 'Updating database...'
python manage.py create_foreign_keys
python manage.py create_indexes
python manage.py create_matviews
