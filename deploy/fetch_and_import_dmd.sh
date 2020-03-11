#!/bin/bash
. /webapps/openprescribing/.venv/bin/activate
python /webapps/openprescribing/openprescribing/manage.py fetch_dmd
python /webapps/openprescribing/openprescribing/manage.py fetch_bnf_snomed_mapping
python /webapps/openprescribing/openprescribing/manage.py import_dmd
