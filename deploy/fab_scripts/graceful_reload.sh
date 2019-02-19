#!/bin/bash

set -e

script_dir="$( unset CDPATH && cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
pid_file="$script_dir/../../run/gunicorn.pid"

PID=$(cat "$pid_file")
if [[ -n "$PID" ]]; then
    kill -HUP $PID;
else
    echo "Error: server $1 not running, so could not reload";
    exit 1;
fi
