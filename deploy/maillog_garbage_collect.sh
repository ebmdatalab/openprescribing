#!/bin/bash
. /webapps/openprescribing/.venv/bin/activate
python /webapps/openprescribing/openprescribing/manage.py maillog_garbage_collect
