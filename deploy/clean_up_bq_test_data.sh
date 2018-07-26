#!/bin/bash
export DJANGO_SETTINGS_MODULE=openprescribing.settings.test
LOGFILE=$(mktemp -t clean_up_bq_test_data-$(date +%Y-%m-%d)-XXXX.log)

. /webapps/openprescribing/.venv/bin/activate

python /webapps/openprescribing/openprescribing/manage.py clean_up_bq_test_data >$LOGFILE 2>&1
