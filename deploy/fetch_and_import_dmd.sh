#!/bin/bash
. /webapps/openprescribing/.venv/bin/activate
python /webapps/openprescribing/openprescribing/manage.py fetch_dmd
python /webapps/openprescribing/openprescribing/manage.py import_dmd
