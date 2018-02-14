#!/bin/bash
export DJANGO_SETTINGS_MODULE=openprescribing.settings.test
. /webapps/openprescribing/.venv/bin/activate
python /webapps/openprescribing/openprescribing/manage.py clean_up_bq_test_data
