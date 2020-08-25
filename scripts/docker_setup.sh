#!/bin/bash

# Commands that should be run before starting a docker-based
# application session via docker-compose

python ./scripts/wait_for_postgres.py
pip install -q -U pip setuptools
pip install -q -r requirements.txt
if ! [ -r openprescribing/media/js/node_modules ]; then
    ln -s /npm/node_modules openprescribing/media/js/
else
    echo "NOTICE: node_modules already exists in repo; refusing to use the node_modules provided by the docker image"
fi
mkdir logs
cd openprescribing/media/js
npm cache clean
npm install -s
