s[![Build Status](https://travis-ci.org/ebmdatalab/openprescribing.svg?branch=master)](https://travis-ci.org/ebmdatalab/openprescribing)
[![Code Climate](https://codeclimate.com/github/ebmdatalab/openprescribing.png)](https://codeclimate.com/github/ebmdatalab/openprescribing)

# Open Prescribing

Website code for https://openprescribing.net - a Django application that provides a REST API and dashboards for the HSCIC's [GP-level prescribing data](http://www.hscic.gov.uk/searchcatalogue?q=title%3a%22presentation+level+data%22&sort=Relevance&size=100&page=1#top)

# Set up the application

You can install the application dependencies either on bare metal, or
using docker.

## Using docker

Install `docker` and `docker-compose` per
[the instructions](https://docs.docker.com/compose/install/) (you need
at least Compose 1.6.0+ and Docker Engine of version 1.10.0+.)

In the project root, run

    docker-compose run test

This will pull down the relevant images, and run the tests.

To open a shell (from where you can run migrations, start a server,
etc), run

    docker-compose run dev

The project code is mounted as a volume within the docker container,
at `/code/openprescribing`. Note that the container runs as the `root`
user, so any files you create from that console will be owned by
`root`.

The first time you run `docker-compose` it creates a persistent volume
for the postgres container. Therefore, if you ever need to change the
database configuration, you'll need to blow away the volume with:

    docker-compose stop
    docker-compose rm -f all

Any time you change the npm or pip dependencies, you should rebuild
the docker image used by the tests:

    docker build -t ebmdatalab/openprescribing-base .
    docker login  # details in `pass`; only have to do this once on your machin
    docker push  # pushes the image to hub.docker.io

## On bare metal

### Set up a virtualenv

If you're using [virtualenvwrapper](https://virtualenvwrapper.readthedocs.org/en/latest/):

    mkvirtualenv openprescribing
    cd openprescribing && add2virtualenv `pwd`
    workon openprescribing

### Install dependencies

Install Python dependencies in development:

    pip install -r requirements/local.txt

Or in production:

    pip install -r requirements.txt

And then install JavaScript dependencies. You'll need a version of
nodejs greater than v0.10.11:

    cd openprescribing/media/js
    npm install -g browserify
    npm install -g jshint
    npm install

### Create database and env variables

Set up a Postgres 9.4 database (required for `jsonb` type), with
PostGIS extensions, and create a superuser for the database.

    createuser -s <myuser>
    createdb -O <myuser> <dbname>
    psql -d <dbname> -c "CREATE EXTENSION postgis;"

Set the `DB_NAME`, `DB_USER`, and `DB_PASS` environment variables based on the database login you used above.

Set the `CF_API_EMAIL` and `CF_API_KEY` for Cloudflare (this is only required for automated deploys, see below).

You will need a `GMAIL_PASS` environment variable to send error emails in production. In development you will only need this to run tests, so you can set this to anything.

Finally set a `SECRET_KEY` environment variable (make this an SSID).

# Set up the database

Run migrations:

    python manage.py migrate

# Run tests

Run Django and JavaScript tests:

    make test

If required, you can run individual Django tests as follows:

    python manage.py test frontend.tests.test_api_views

# Run the application

    python manage.py runserver --settings=openprescribing.settings.local

You should now have a Django application running with no data inside it.

# Load the HSCIC data

Run setup.sh to fetch and import data, and create the indexes and materialized views needed to set up the database.

    chmod u+x ../setup.sh
    ../setup.sh

This is likely to take many hours to run, and will fetch more than 100GB of data. You probably want to tweak Postgres's memory settings first.

If you just want to import one month of data to get started, edit setup.sh to use `--filename` arguments (as below in 'Updating the data').

# Editing JS and CSS

Source JavaScript is in `/media`, compiled JavaScript is in `/static`.

During development, run the `watch` task to see changes appear in the compiled JavaScript.

    cd openprescribing/media/js
    npm run watch

And run tests with:

    npm run test

Before deploying, run the build task to generate minified JavaScript:

    npm run build

Similarly, you can build the compiled CSS from the source LESS with:

    npm run build-css

# Deployment

Deployment is carried out using [`fabric`](http://www.fabfile.org/).

Your public key must be added to `authorized_keys` for the `hello`
user, and SSH forwarding should work (this possibly means running
`ssh-agent add <private-key>` on your workstation - see
[this helpful debugging guide](https://developer.github.com/guides/using-ssh-agent-forwarding/)
if you are having problems.

Running `fab deploy:production` will:


* Check if there are any changes to deploy
* Install `npm` and `pip` as required (you will need sudo access to do this)
* Update the repo on the server
* Install any new pip and npm dependencies
* Build JS and CSS artefacts
* Run pending migations (only for production environment)
* Reload the server gracefully
* Clear the cloudflare cache
* Log a deploy to `deploy-log.json` in the deployment directory on the server

You can also deploy to staging:

    fab deploy:staging

Or deploy a specific branch to staging:

    fab deploy:staging,branch=my_amazing_branch

If the fabfile detects no undeployed changes, it will refuse to run. You can force it to do so (for example, to make it rebuild assets), with:

    fab deploy:production,force_build=true

Or for staging:

    fab deploy:staging,force_build=true,branch=deployment

# Updating the data

You may need to add data for new months. To do this, active your virtualenv, then wget the files you need from the HSCIC site. Also, get the latest versions of `eccg.csv` and `epraccur.csv` from the [HSCIC site](http://systems.hscic.gov.uk/data/ods/datadownloads/index).

Note that the ordering of the following steps is important.

Start by updating organisational data. The first and third steps only need to be run if `epraccur.csv` and `eccg.csv` have changed:

    python manage.py import_org_names --ccg data/org_codes/eccg.csv -v 2
    python manage.py import_practices --hscic_address data/raw_data/[ADDR FILE].CSV -v 2
    python manage.py import_practices --epraccur data/org_codes/epraccur.csv -v 2

If new practices were added at any point, re-run the practice geocoder, with the latest version of the `gridall.csv` file, which you can also obtain from the HSCIC site:

    python manage.py geocode_practices -v 2 --filename data/gridall.csv

Import the chemicals:

    python manage.py import_hscic_chemicals --chem_file data/raw_data/[CHEM FILE].CSV -v 2

Now you can convert and import the prescribing data:

    python manage.py convert_hscic_prescribing --filename data/raw_data/[PDPI FILE].CSV -v 2
    python manage.py import_hscic_prescribing --filename data/raw_data/[PDPI FORMATTED FILE].CSV -v 2

Then update list sizes for the latest months. You can get the raw list size data from deep inside the NHS BSA Information Portal:

    python manage.py import_list_sizes --filename data/list_sizes/[MONTH FILE].CSV -v 2

(If you want to add list size data for only part of a quarter - which will be the case if the HSCIC file is not for the last month of a quarter - then rename the filename to cover only those months.)

Then update measures. You can get the raw list size data from the [BSA Information Portal](https://apps.nhsbsa.nhs.uk/infosystems/welcome) (Report > Common Information Reports > Organisation Data > Practice List Size):

    python manage.py import_measures --start_date YYYY-MM-DD --end_date YYYY-MM-DD -v 2

Finally, refresh the materialized views (which will take some time, and slow the database while it runs - if doing this remotely, it's best to run this inside a screen session):

    python manage.py refresh_matviews -v 2

Now purge the CloudFlare cache and you should see the new data appear.

You may now want to run a snapshot on the DigitalOcean server, for use in backups if ever needed. This will take down the server for a few hours, so is best done in the middle of the night.

And finally, update the smoke tests in `smoke.py` - you'll need to update `NUM_RESULTS`, plus add expected values for the latest month.

Then re-run the smoke tests against the live data to make sure everything looks as you expect:

    python smoketests/smoke.py

# Philosophy

This project follows design practices from [Two Scoops of Django](http://twoscoopspress.org/products/two-scoops-of-django-1-6).
