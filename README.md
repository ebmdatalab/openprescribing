[![Build Status](https://travis-ci.org/ebmdatalab/openprescribing.svg?branch=master)](https://travis-ci.org/ebmdatalab/openprescribing)
[![Code Climate](https://codeclimate.com/github/ebmdatalab/openprescribing.png)](https://codeclimate.com/github/ebmdatalab/openprescribing)

# Open Prescribing

Website code for https://openprescribing.net - a Django application that provides a REST API and dashboards for the NHS Digitals's [GP-level prescribing data](http://content.digital.nhs.uk/searchcatalogue?q=title%3A%22presentation+level+data%22&area=&size=10&sort=Relevance) and [NHS BSA's Detailed Prescribing Information Report](https://apps.nhsbsa.nhs.uk/infosystems/welcome).

Information about data sources used on OpenPrescribing can be found [here](https://openprescribing.net/about/)

# Set up the application

You can install the application dependencies either on bare metal, or
virtualised inside docker, or virtualbox (via vagrant).

Which to use?

* The vagrant route is probably the easiest. It creates a virtual
  Debian server and then uses `ansible` to install all the dependencies
  for you.
* We currently deploy the site to production on bare metal, though we
  may well switch to using ansible in the medium term. Use this route
  if you don't want to mess around with virtualisation for some
  reason.
* Our tests are run in Travis using Docker - they have to, because
  there's no pre-built postgis docker environment.  Use this route to
  reproduce the travis test environment exactly (i.e. you probably
  don't want to use this route!)

## Using vagrant

Requires [Vagrant](https://www.vagrantup.com/downloads.html) and [VirtualBox](https://www.virtualbox.org/wiki/Downloads)

### Provision the vagrant box


    cd openprescribing/ansible
    vagrant up   # invokes `vagrant provision` the first time it's run

### Start the server

    vagrant ssh  # also activates the virtualenv for you
    python manage.py runserver_plus 0.0.0.0:8000

The application should then be accessible at
``http://127.0.0.1:3333/`` (using the vagrant-forwarded port) from a
web browser on the host computer.

## Using bare metal

This should be enough to get a dev sandbox running; some brief notes
about production environment follow.

### Set up a virtualenv

If you're using [virtualenvwrapper](https://virtualenvwrapper.readthedocs.org/en/latest/):

    mkvirtualenv openprescribing
    cd openprescribing && add2virtualenv `pwd`
    workon openprescribing

### Install dependencies

Install library dependencies (current as of Debian Jessie):

    sudo apt-get install nodejs binutils libproj-dev gdal-bin libgeoip1 libgeos-c1 git-core vim sudo screen supervisor libpq-dev python-dev python-pip python-virtualenv python-gdal postgis emacs nginx build-essential libssl-dev libffi-dev unattended-upgrades libblas-dev liblapack-dev libatlas-base-dev gfortran libxml2-dev libxslt1-dev

Ensure pip and setuptools are up to date:

    pip install -U pip setuptools

Install Python dependencies:

    pip install -r requirements.txt

And then install JavaScript dependencies. Make sure you have the latest version
of nodejs:

    cd openprescribing/media/js
    npm install -g browserify
    npm install -g jshint
    npm install -g less
    npm install

To generate monthly alert emails (and run the tests for those) you'll
need a `phantomjs` binary located at `/usr/local/bin/phantomjs`. Get
it from [here](http://phantomjs.org/download.html).

### Create database and env variables

Set up a Postgres 9.5 database (required for `jsonb` type), with
PostGIS extensions, and create a superuser for the database.

    createuser -s <myuser>
    createdb -O <myuser> <dbname>
    psql -d <dbname> -c "CREATE EXTENSION postgis;"

Copy `environment-sample` to `environment`, and set the `DB_*` environment variables.

Set the `CF_API_EMAIL` and `CF_API_KEY` for Cloudflare (this is only required for automated deploys, see below).

You will want `MAILGUN_WEBHOOK_USER` and `MAILGUN_WEBHOOK_PASS` if you want to process Mailgun webhook callbacks (see [`TRACKING.md`](./TRACKING.md)) to match the username/password configured in Mailgun. For example, if the webhook is

    http://bobby:123@openprescribing.net/anymail/mailgun/tracking/

Then set `MAILGUN_WEBHOOK_USER` to `bobby` and `MAILGUN_WEBHOOK_PASS` to `123`.


## Using docker

Install `docker` and `docker-compose` per
[the instructions](https://docs.docker.com/compose/install/) (you need
at least Compose 1.9.0+ and Docker Engine of version 1.12.0+.)

In the project root, run

    docker-compose run test

This will pull down the relevant images, and run the tests.  In order for all
tests to run successfully, you will also need to decrypt the credentials file
openprescribing/google-credentials.json.

In our CI system, we also run checks against the production environment, which
you can reproduce with

    docker-compose run test-production

To open a shell (from where you can run migrations, start a server,
etc), run

    docker-compose run --service-ports dev

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
the docker image used by the tests to improve runtime performance of
travis.

    # Base docker image, for production
    docker build -t ebmdatalab/openprescribing-base .
    # Same as base, but with local-only pip dependencies
    docker build -t ebmdatalab/openprescribing-test -f Dockerfile-test .
    docker login  # details in `pass`; only have to do this once on your machin
    # push the images to hub.docker.io
    docker push ebmdatalab/openprescribing-base
    docker push ebmdatalab/openprescribing-test


### Running the application from within Docker
To be able to access the django instance running inside Docker from outside the container, docker must be told to publish the port on which Django will listen:

    docker-compose run --service-ports dev

This will give a shell, at which you can start Django, specifying the ``0.0.0.0`` interface so that it will accept connections from all IP addesses (not just localhost):

     python manage.py runserver_plus 0.0.0.0:8000

The application should then be accessible at ``http://localhost:8000/`` from a web-
on the host computer.


## Production notes

Secrets are stored in the `environment` file, and are loaded in
Django's `manage.py` using the `django-dotenv` package.

The script at `bin/gunicorn_start` is responsible for starting
up a backend server. We proxy to this from nginx using a configuration
like that at `contrib/supervisor/nginx/`.  We control the gunicorn process using
`supervisor`, with a script like that at `contrib/supervisor/`.

# Set up the database

Run migrations:

    python manage.py migrate

## Sandbox data

You can copy everything from the production server, if you want, but
the full set of prescribing data is enormous. To get a sample of that,
run the following on production:

    mkdir /tmp/sample
    ./manage sample_data dump --dir /tmp/sample

Copy that to a local location (e.g. `/tmp/sample` again), then run:

    ./manage sample_data load --dir /tmp/sample

By default, the `dump` invocation extracts data relating to the CCG
`09X`, but you can override that with the `--ccg` switch.

# Run tests

Run Django and JavaScript tests:

    make test

If required, you can run individual Django tests as follows:

    python manage.py test frontend.tests.test_api_views

We support IE9 and above. We have a free account for testing across
multiple browsers, thanks to [BrowserStack](www.browserstack.com).

![image](https://user-images.githubusercontent.com/211271/29110431-887941d2-7cde-11e7-8c2f-199d85c5a3b5.png)

Note that tests are run using the settings in
`openprescribing/settings/test.py`; this happens automatically

## Functional tests

Functional tests are run using Selenium; the default in your sandbox
is to do so via a Firefox driver, so you will need Firefox
installed. Running the functional tests will therefore result in a
browser being launched.

If you want to run the tests headless (i.e. without launching a
browser), you have two choices:

### Run the functional tests using Xvbf

To do this, you'll need to install
[pyvirtualdisplay](http://pyvirtualdisplay.readthedocs.io/en/latest/#installation)
and Xvbf. This is, apparently, quite hard to do on OS X.

If you don't install Xvbf, you'll see the tests launch a browser and
operate it.

You can run *just* the functional tests with

    TEST_SUITE=functional make test

And the inverse is:

    TEST_SUITE=nonfunctional make test

### Run the functional tests in Saucelabs

In our CI environment we use [Saucelabs](http://saucelabs.com) to run
the functional tests in various browsers. If you are connected to the
internet, you can run these tests against Saucelabs by
[installing Sauce Connect](https://wiki.saucelabs.com/display/DOCS/Setting+Up+Sauce+Connect),
and running:

    # Start the Sauce Connect proxy
    ./sc -u $SAUCE_USERNAME -k $SAUCE_ACCESS_KEY

    # Run the tests using Saucelabs
    USE_SAUCELABS=1 BROWSER="firefox:47:Windows 2012" make test

You can work out the browser string to use for your desired platform /
browser combination using
[this Saucelabs tool](https://wiki.saucelabs.com/display/DOCS/Platform+Configurator#/).
You can find the combinations we use for our Travis CI in
[`.travis.yml`](.travis.yml).

### Skip the functional tests

    TEST_SUITE=nonfunctional make test

# Run the application

    python manage.py runserver_plus

You should now have a Django application running with no data inside it.

# Load the HSCIC data

Check out the `openprescribing-data` repo (which contains data for the
app, and scripts to update that data):

    git clone git@github.com:ebmdatalab/openprescribing-data.git

Follow the documentation there to import data.

# Editing JS and CSS

Source JavaScript is in `/media`, compiled JavaScript is in `/static`.

During development, run the `watch` task to see changes appear in the
compiled JavaScript and CSS.

    cd openprescribing/media/js
    npm run watch

The client-side code makes extensive use of data from the API. To test client-side code against production data, you can set an environment variable to use an API host other than the default:

    API_HOST=https://openprescribing.net npm run watch

And run tests with:

    npm run test

This build task generates production-ready minified JavaScript, CSS
etc, and is executed as part of the fabric deploy process:

    npm run build

If you add new javascript source files, update the `modules` array at
`media/js/build.js`.

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

# Development

Various hooks can be run before committing.  Pre-commit hooks are managed by https://github.com/pre-commit/pre-commit-hooks.

To install the hooks, run once:

    pre-commit install

Details of the hooks are in .pre-commit-config.yaml

# Philosophy

This project follows design practices from [Two Scoops of Django](http://twoscoopspress.org/products/two-scoops-of-django-1-6).
