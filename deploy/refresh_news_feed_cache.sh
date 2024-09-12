#!/bin/bash
. /webapps/openprescribing/.venv/bin/activate
python /webapps/openprescribing/openprescribing/manage.py refresh_news_feed_cache
