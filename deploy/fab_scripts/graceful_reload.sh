#!/bin/bash

set -e

PID=$(cat /webapps/openprescribing/run/gunicorn.pid)
if [[ -n "$PID" ]]; then
    kill -HUP $PID;
else
    echo "Error: server $1 not running, so could not reload";
    exit 1;
fi
