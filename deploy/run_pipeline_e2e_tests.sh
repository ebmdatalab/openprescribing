#!/bin/bash
export DJANGO_SETTINGS_MODULE=openprescribing.settings.e2etest
LOGFILE=$(mktemp -t e2e-$(date +%Y-%m-%d)-XXXX.log)

. /webapps/openprescribing/.venv/bin/activate

PGPASSWORD=$DB_PASS dropdb -U $DB_USER $E2E_DB_NAME 
PGPASSWORD=$DB_PASS createdb -U $DB_USER $E2E_DB_NAME 

python /webapps/openprescribing/openprescribing/manage.py migrate 2>&1 >$LOGFILE
python /webapps/openprescribing/openprescribing/manage.py pipeline_e2e_tests 2>&1 >$LOGFILE
