#!/bin/bash

set -e -o pipefail

# Install ansible dependencies
cd /openprescribing/ansible
apt-get update && apt-get -qq -y install locales curl python
curl https://bootstrap.pypa.io/get-pip.py | python
/usr/local/bin/pip install -r vagrant_requirements.txt

# Set up the locale we use in postgres
sed -i 's/^# *\(en_US.UTF-8\)/\1/' /etc/locale.gen && locale-gen

# Run the playbook
/usr/local/bin/ansible-playbook -v travis.yml

# Do minimal database-connection test
su -c 'SKIP_NPM_BUILD=1 /openprescribing/venv/bin/python /openprescribing/openprescribing/manage.py test frontend.tests.test_models.SearchBookmarkTestCase' vagrant
