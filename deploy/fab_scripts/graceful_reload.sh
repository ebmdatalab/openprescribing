#!/bin/bash

set -e

script_dir="$( unset CDPATH && cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

case "$script_dir" in
  /webapps/openprescribing/*)
    app_name=openprescribing
  ;;
  /webapps/openprescribing_staging/*)
    app_name=openprescribing_staging
  ;;
  *)
    echo "Error: can't determine which environment script is running in"
    exit 1
  ;;
esac

# Service names follow the pattern:
#
#   app.<APP_NAME>.<PROCESS_NAME>.service
#
# The "app" prefix serves to namespace our services off from any other system services.
#
# APP_NAME is the name of this particular deployment of an application. If a
# single project (e.g. openprescribing) is deployed in multiple environments
# (e.g. production, staging) then each environment gets its own app name.
#
# A single application may have multiple processes and hence multiple services
# wtih different PROCESS_NAMEs.  By convention (established by Heroku) the
# process that runs the web application is called "web".
#
# The "service" suffix comes from systemd. Services which want systemd to
# manage a socket for them (to allow for graceful restarts) will also have a
# corresponding ".socket" configuration file to go with the ".service" file.
#
# Because many systemd commands allow the use of wildcards, this dotted-name
# convention makes it easy to do things like "restart all services for this
# app".
service_name="app.$app_name.web.service"

service_enabled=false
if systemctl list-unit-files --type service --state enabled | grep -Fq "$service_name"; then
  service_enabled=true
fi

# Vary the restart behaviour depending on whether or not the corresponding
# systemd service is enabled
if $service_enabled; then
  systemctl restart "$service_name"
else
  pid_file="$script_dir/../../run/gunicorn.pid"
  PID=$(cat "$pid_file")
  if [[ -n "$PID" ]]; then
      kill -HUP $PID;
  else
      echo "Error: server $1 not running, so could not reload";
      exit 1;
  fi
fi
