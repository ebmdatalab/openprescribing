# coding=utf8

'''
Checks whether any numbers displayed on a selection of URLs on the site have
changed since the command was last run, to help detect bugs affecting accuracy
of calculations.

It is designed to be run immediately after deployment (see fabfile.py), and
will report any changes to Slack.

We do expect the numbers appearing on the site to change after importing data,
so (a) we don't check if an import is in progress, and (b) the import process
deletes old records of numbers.
'''

import json
import os
import re
from datetime import datetime
from glob import glob
from time import sleep

from django.conf import settings
from django.core.management import BaseCommand
from django.core.urlresolvers import get_resolver

from bs4 import BeautifulSoup
from selenium import webdriver

from openprescribing.utils import mkdir_p
from pipeline.runner import in_progress as import_in_progress


class Command(BaseCommand):
    help = __doc__

    def handle(self, *args, **options):
        if import_in_progress():
            notify_slack('Not checking numbers: import in progress')
            return

        previous_log_path = get_previous_log_path()

        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        log_path = os.path.join(settings.CHECK_NUMBERS_BASE_PATH, timestamp)
        mkdir_p(log_path)

        with webdriver.Firefox() as browser:
            numbers = {
                name: {
                    'path': path,
                    'numbers': extract_numbers(browser, path, name, log_path),
                }
                for name, path in get_paths_to_scrape()
            } 

        write_numbers(numbers, log_path)

        if previous_log_path is None:
            msg = 'Not checking numbers: this is the first deploy since last import'
            notify_slack(msg)
            return

        previous_numbers = load_previous_numbers(previous_log_path)

        differences = compare_numbers(previous_numbers, numbers)

        if differences:
            msg = 'The following pages have changed:\n\n'
            msg += '\n'.join(differences)
            msg += '\n\nNext step: compare {} and {}'.format(previous_log_path, log_path)
            notify_slack(msg)


def get_paths_to_scrape():
    '''Yield paths that should be scraped.

    We're interested in a sample of all pages for organisations.  Rather than
    specify pages we're interested in, we ignore pages we're not interested in.
    '''

    # Don't scrape URLs beginning with these prefixes.
    prefixes_to_ignore = [
        'accounts',
        'admin',
        'api',
        'bnf',
        'bookmarks',
        'chemical',
        'dmd',
        'docs',
    ]

    # get_resolver().reverse_dict is a dict that maps view names or view
    # functions to a data structure that describes how requests should be
    # dispatched.
    for k, v in get_resolver().reverse_dict.items():

        # Ignore records where the key is a view function.
        if not isinstance(k, str):
            continue

        name = k
        pattern = v[0][0][0]
        keys = v[0][0][1]

        # Ignore records starting with prefixes we're not interested in.
        if any(pattern.startswith(prefix) for prefix in prefixes_to_ignore):
            continue

        # Ignore any URLs that 
        if '%' not in pattern and 'all-england' not in pattern:
            continue

        path = bulid_path(pattern, keys)
        yield name, path


def bulid_path(pattern, keys):
    '''Replace placeholders in `pattern` to build path to be scraped.

    `pattern` will be a string like "measure/%(measure)s/ccg/%(entity_code)s/".
    '''

    substitutions = {
        'practice_code': 'L83100',
        'ccg_code': '15N',
        'stp_code': 'E54000037',
        'regional_team_code': 'Y58',
        'bnf_code': '0205051R0BBAIAN',
        'measure': 'ace',
    }

    path = pattern

    for key in keys:
        subst_key = None

        if key in ['code', 'entity_code']:
            for token in ['practice', 'ccg', 'stp', 'regional-team']:
                if token in pattern:
                    subst_key = '{}_code'.format(token).replace('-', '_')
            if subst_key is None:
                subst_key = 'bnf_code'
        else:
            subst_key = key

        path = path.replace(
            '%({})s'.format(key), 
            substitutions[subst_key]
        )

    assert '%' not in path, 'Could not interpolate ' + name

    return path


def extract_numbers(browser, path, name, log_path):
    '''Request URL, write copy of response to log_path, and return list of
    anything that looks like an interesting number in the response.
    '''

    url = 'https://openprescribing.net/' + path
    browser.get(url)

    # Wait until all AJAX requests are complete.
    while browser.execute_script('return jQuery.active > 0'):
        sleep(0.1)

    source = browser.page_source

    with open(os.path.join(log_path, name + '.html'), 'w') as f:
        f.write(source.encode('utf8'))

    doc = BeautifulSoup(source, 'html.parser')
    body = doc.find('body')

    # The SVG charts contain all sorts of things that look like numbers (eg
    # rgb(255,255,255)) so we drop all <svg> elements.
    for tag in body.find_all('svg'):
        tag.decompose()

    rx = re.compile(u'''
        £[\d,\.]+           # Anything that looks like a cost
        |                   # ...or...
        \d{1,3}(?:,\d{3})+  # anything that looks like a humanized number
        ''',
        re.VERBOSE
    )
    return rx.findall(body.text)


def compare_numbers(previous_numbers, numbers):
    '''Compare dictionaries of numbers, returning list of any differences.
    '''

    differences = []
    
    for name in previous_numbers:
        if name not in numbers:
            path = previous_numbers[name]['path']
            differences.append('Missing: {} ({})'.format(name, path))
    
    for name in numbers:
        if name not in previous_numbers:
            path = numbers[name]['path']
            differences.append('Added: {} ({})'.format(name, path))

        elif numbers[name]['numbers'] != previous_numbers[name]['numbers']:
            path = numbers[name]['path']
            differences.append('Changed: {} ({})'.format(name, path))

    return differences


def get_previous_log_path():
    '''Return path to directory with most recent numbers.json, or None if it
    does not exist.

    If no such file exists, this is probably the first run since an import.
    '''

    paths = glob(os.path.join(settings.CHECK_NUMBERS_BASE_PATH, '*', 'numbers.json'))
    if not paths:
        return None

    return os.path.dirname(sorted(paths)[-1])


def write_numbers(numbers, log_path):
    '''Write scraped numbers from this run.'''

    with open(os.path.join(log_path, 'numbers.json'), 'w') as f:
        json.dump(numbers, f, indent=2)


def load_previous_numbers(previous_log_path):
    '''Load scraped numbers from previous run.'''

    with open(os.path.join(previous_log_path, 'numbers.json')) as f:
        return json.load(f)
