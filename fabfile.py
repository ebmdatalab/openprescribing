from fabric.api import run, sudo, prefix, warn, abort
from fabric.api import settings, task, env
from fabric.context_managers import cd

from datetime import datetime
import json
import os
import requests


env.hosts = ['46.101.62.45']
env.forward_agent = True
env.colorize_errors = True
env.user = 'hello'

environments = {
    'production': 'openprescribing',
    'staging': 'openprescribing_staging'
}

# This zone ID may change if/when our account changes
# Run `fab list_cloudflare_zones` to get a full list
ZONE_ID = "a0965a9865f3c77f44fa06569fcfa714"


def git_init():
    run('git init . && '
        'git remote add origin '
        'git@github.com:ebmdatalab/openprescribing.git && '
        'git fetch origin && '
        'git branch --set-upstream master origin/master')


def venv_init():
    run('virtualenv .venv')


def git_pull():
    run('git fetch --all')
    run('git checkout --force origin/%s' % env.branch)


def pip_install():
    if filter(lambda x: x.startswith('requirements'),
                       [x for x in env.changed_files]):
        with prefix('source .venv/bin/activate'):
            run('pip install -r requirements/production.txt')


def npm_install():
    installed = run("if [[ -n $(which npm) ]]; then echo 1; fi")
    if not installed:
        sudo('curl -sL https://deb.nodesource.com/setup_6.x |'
             'bash - && apt-get install -y  '
             'nodejs binutils libproj-dev gdal-bin libgeoip1 libgeos-c1;',
             user=env.local_user)
        sudo('npm install -g browserify && npm install -g eslint',
             user=env.local_user)


def npm_install_deps(force=False):
    if force or 'openprescribing/media/js/package.json' in env.changed_files:
        run('cd openprescribing/media/js && npm install')


def npm_build_js(force=False):
    if force or filter(lambda x: x.startswith('openprescribing/media/js'),
                       [x for x in env.changed_files]):
        run('cd openprescribing/media/js && npm run build')


def npm_build_css(force=False):
    if force or filter(lambda x: x.startswith('openprescribing/media/css'),
                       [x for x in env.changed_files]):
        run('cd openprescribing/media/js && npm run build-css')


def purge_urls(paths_from_git, changed_in_static):
    """Turn 2 lists of filenames (changed in git, and in static) to a list
    of URLs to purge in Cloudflare.

    """
    urls = []
    if env.environment == 'production':
        base_url = 'https://openprescribing.net'
    else:
        base_url = 'http://staging.openprescribing.net'

    static_templates = {
        'openprescribing/templates/index.html': '',
        'openprescribing/templates/api.html': 'api/',
        'openprescribing/templates/about.html': 'about/',
        'openprescribing/templates/caution.html': 'caution/',
        'openprescribing/templates/how-to-use.html': 'how-to-use/'
    }
    for name in changed_in_static:
        if name.startswith('openprescribing/static'):
            urls.append("%s/%s" %
                        (base_url,
                         name.replace('openprescribing/static/', '')))

    for name in paths_from_git:
        if name in static_templates:
            urls.append("%s/%s" % (base_url, static_templates[name]))
    return urls


def log_deploy():
    url = "https://github.com/ebmdatalab/openprescribing/compare/%s...%s"
    current_commit = run("git rev-parse --verify HEAD")
    log_line = json.dumps({'started_at': str(env.started_at),
                           'ended_at': str(datetime.utcnow()),
                           'changes_url': url % (env.previous_commit,
                                                 current_commit)})
    run("echo '%s' >> deploy-log.json" % log_line)


def checkpoint(force_build):
    env.started_at = datetime.utcnow()
    with settings(warn_only=True):
        inited = run('git status').return_code == 0
        if not inited:
            git_init()
        if run('file .venv').return_code > 0:
            venv_init()
    env.previous_commit = run('git rev-parse --verify HEAD')
    run('git fetch')
    env.next_commit = run('git rev-parse --verify origin/%s' % env.branch)
    env.changed_files = set(
        run("git diff --name-only %s %s" %
            (env.previous_commit, env.next_commit), pty=False)
        .split())
    if not force_build and env.next_commit == env.previous_commit:
        abort("No changes to pull from origin!")


def run_migrations():
    if env.environment == 'production':
        with prefix('source .venv/bin/activate'):
            run('cd openprescribing/ && python manage.py migrate '
                '--settings=openprescribing.settings.production')
    else:
        warn("Refusing to run migrations in staging environment")


@task
def graceful_reload():
    result = run(r"""PID=$(sudo supervisorctl status | grep %s |
    sed -n '/RUNNING/s/.*pid \([[:digit:]]\+\).*/\1/p');
    if [[ -n "$PID" ]]; then kill -HUP $PID;
    else echo "Error: server %s not running, so could not reload";
    exit 1; fi""" % (env.app, env.app))
    if result.failed:
        # Use the error from the bash command(s) rather than rely on
        # noisy (and hard-to-interpret) output from fabric
        abort(result)


def find_changed_static_files():
    changed = run(
        "find %s/openprescribing/static -type f -newermt '%s'" %
        (env.path, env.started_at.strftime('%Y-%m-%d %H:%M:%S'))).split()
    return map(lambda x: x.replace(env.path + '/', ''), [x for x in changed])


@task
def list_cloudflare_zones():
    url = 'https://api.cloudflare.com/client/v4/zones'
    headers = {
        "Content-Type": "application/json",
        "X-Auth-Key": os.environ['CF_API_KEY'],
        "X-Auth-Email": os.environ['CF_API_EMAIL']
    }
    result = json.loads(
        requests.get(url, headers=headers,).text)
    zones = map(lambda x: {'name': x['name'], 'id': x['id']},
                [x for x in result["result"]])
    print json.dumps(zones, indent=2)


def clear_cloudflare(purge_all=False):
    url = 'https://api.cloudflare.com/client/v4/zones/%s'
    headers = {
        "Content-Type": "application/json",
        "X-Auth-Key": os.environ['CF_API_KEY'],
        "X-Auth-Email": os.environ['CF_API_EMAIL']
    }
    if purge_all:
        data = {'purge_everything': True}
    else:
        # XXX need to think about these. If we're looking at files
        # that have changed since the deployment started, do we need
        # to bother with files that have changed according to git?
        changed_files_from_git = env.changed_files.copy()
        data = {'files': purge_urls(changed_files_from_git,
                                    find_changed_static_files())}

    print "Purging from Cloudflare:"
    print data
    result = json.loads(
        requests.delete(url % ZONE_ID + '/purge_cache',
                        headers=headers, data=json.dumps(data)).text)
    if result['success']:
        print "Cloudflare clearing succeeded: %s" % \
            json.dumps(result, indent=2)
    else:
        warn("Cloudflare clearing failed: %s" %
             json.dumps(result, indent=2))


@task
def deploy(environment, force_build=False, branch='master'):
    if environment not in environments:
        abort("Specified environment must be one of %s" %
              ",".join(environments.keys()))
    env.app = environments[environment]
    env.environment = environment
    env.path = "/webapps/%s" % env.app
    env.branch = branch
    with cd(env.path):
        checkpoint(force_build)
        git_pull()
        pip_install()
        npm_install()
        npm_install_deps(force_build)
        npm_build_js(force_build)
        npm_build_css(force_build)
        run_migrations()
        graceful_reload()
        clear_cloudflare()
        log_deploy()
