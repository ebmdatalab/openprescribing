#!/bin/bash
. /webapps/openprescribing/.venv/bin/activate
python /webapps/openprescribing/openprescribing/manage.py fetch_drug_tariff --settings=openprescribing.settings.production
