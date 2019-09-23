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

service_name="app.$app_name.web.service"

systemctl restart "$service_name"
