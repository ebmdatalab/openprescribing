[![Build Status](https://travis-ci.org/ebmdatalab/openprescribing.svg?branch=master)](https://travis-ci.org/ebmdatalab/openprescribing)
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

We support IE8 and above. We have a free account for testing across
multiple browsers, thanks to [BrowserStack](www.browserstack.com).

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

    python manage.py runserver_plus --settings=openprescribing.settings.local

You should now have a Django application running with no data inside it.

# Load the HSCIC data

Check out the `openprescribing-data` repo (which contains data for the
app, and scripts to update that data):

    git clone git@github.com:ebmdatalab/openprescribing-data.git

Follow the documentation there to import data.

# Editing JS and CSS

Source JavaScript is in `/media`, compiled JavaScript is in `/static`.

During development, run the `watch` task to see changes appear in the compiled JavaScript.

    cd openprescribing/media/js
    npm run watch

The client-side code makes extensive use of data from the API. To test client-side code against production data, you can set an environment variable to use an API host other than the default:

    API_HOST=https://openprescribing.net npm run watch

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

# Philosophy

This project follows design practices from [Two Scoops of Django](http://twoscoopspress.org/products/two-scoops-of-django-1-6).
