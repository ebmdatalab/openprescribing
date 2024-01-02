# coding=utf8

"""
Checks whether any numbers displayed on a selection of URLs on the site have
changed since the command was last run, to help detect bugs affecting accuracy
of calculations.

It is designed to be run immediately after deployment (see fabfile.py), and
will report any changes to Slack.

We do expect the numbers appearing on the site to change after importing data,
so (a) we don't check if an import is in progress, and (b) the import process
deletes old records of numbers.
"""

import json
import os
import re
import time
from datetime import datetime
from glob import glob

from bs4 import BeautifulSoup
from django.conf import settings
from django.core.management import BaseCommand
from django.urls import get_resolver
from pipeline.runner import in_progress as import_in_progress
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.firefox.options import Options

from openprescribing.slack import notify_slack
from openprescribing.utils import mkdir_p


class Command(BaseCommand):
    help = __doc__

    def handle(self, *args, **options):
        if import_in_progress():
            notify_slack("Not checking numbers: import in progress")
            return

        previous_log_path = get_previous_log_path()

        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        log_path = os.path.join(settings.CHECK_NUMBERS_BASE_PATH, timestamp)
        mkdir_p(log_path)

        numbers = {}
        options = Options()
        options.headless = True
        with webdriver.Firefox(options=options) as browser:
            browser.set_page_load_timeout(60)

            for name, path in paths_to_scrape():
                source = get_page_source(browser, path, name, log_path)
                numbers_list = extract_numbers(source)
                numbers[name] = {"path": path, "numbers": numbers_list}

        write_numbers(numbers, log_path)

        if previous_log_path is None:
            msg = "Not checking numbers: this is the first deploy since last import"
            notify_slack(msg)
            return

        previous_numbers = load_previous_numbers(previous_log_path)

        differences = compare_numbers(previous_numbers, numbers)

        if differences:
            msg = "The following pages have changed:\n\n"
            msg += "\n".join(differences)
            msg += "\n\nNext step: compare {} and {}".format(
                previous_log_path, log_path
            )
            notify_slack(msg)


def paths_to_scrape():
    """Yield paths that should be scraped.

    We're interested in a sample of all pages for organisations.  Rather than
    specify pages we're interested in, we ignore pages we're not interested in.
    """

    # Don't scrape URLs beginning with these prefixes.  They are either static
    # pages, admin pages, or are unlikely to change in an interesting way.
    prefixes_to_ignore = [
        "accounts",
        "admin",
        "api",
        "bnf",
        "bookmarks",
        "chemical",
        "dmd",
        "docs",
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

        # Ignore any URLs that are not either parameterisable (these static
        # pages or lists of entities) or for All England.
        if "%" not in pattern and "national/england" not in pattern:
            continue

        path = build_path(pattern, keys)
        yield name, path


def build_path(pattern, keys):
    """Replace placeholders in `pattern` to build path to be scraped.

    `pattern` will be a string like "measure/%(measure)s/ccg/%(entity_code)s/".
    """

    substitutions = {
        "practice_code": "L83100",
        "ccg_code": "15N",
        "stp_code": "E54000037",
        "regional_team_code": "Y58",
        "bnf_code": "0205051R0BBAIAN",
        "measure": "ace",
    }

    path = pattern

    for key in keys:
        subst_key = None

        if key in ["code", "entity_code"]:
            for token in ["practice", "ccg", "stp", "regional-team"]:
                if token in pattern:
                    subst_key = "{}_code".format(token).replace("-", "_")
            if subst_key is None:
                subst_key = "bnf_code"
        else:
            subst_key = key

        path = path.replace("%({})s".format(key), substitutions[subst_key])

    assert "%" not in path, "Could not interpolate " + pattern

    return path


def get_page_source(browser, path, name, log_path):
    """Request URL, write copy of response to log_path, and return page source."""

    url = "https://openprescribing.net/" + path
    try:
        browser.get(url)
    except TimeoutException:
        raise RuntimeError("Timed out requesting " + path)

    # Wait until all AJAX requests are complete.
    t0 = time.time()
    while browser.execute_script("return jQuery.active > 0"):
        time.sleep(0.1)
        assert time.time() - t0 < 60, "Timed out checking numbers on {}".format(path)

    source = browser.page_source

    with open(os.path.join(log_path, name + ".html"), "w") as f:
        f.write(source)

    return source


def extract_numbers(source):
    """Parse page source to return anything that looks like an interesting
    number.
    """

    doc = BeautifulSoup(source, "html.parser")
    body = doc.find("body")

    # The SVG charts contain all sorts of things that look like numbers (eg
    # rgb(255,255,255)) so we drop all <svg> elements.
    for tag in body.find_all("svg"):
        tag.decompose()

    rx = re.compile(
        r"""
        £[\d,\.]+           # Anything that looks like a cost
        |                   # ...or...
        &pound;[\d,\.]+     # anything that looks like a cost with an HTML entity
        |                   # ...or...
        \d{1,3}(?:,\d{3})+  # anything that looks like a humanized number
        """,
        re.VERBOSE,
    )
    return rx.findall(body.text)


def compare_numbers(previous_numbers, numbers):
    """Compare dictionaries of numbers, returning list of any differences."""

    differences = []

    for name in previous_numbers:
        if name not in numbers:
            path = previous_numbers[name]["path"]
            differences.append("Missing: {} ({})".format(name, path))

    for name in numbers:
        if name not in previous_numbers:
            path = numbers[name]["path"]
            differences.append("Added: {} ({})".format(name, path))

        elif numbers[name]["numbers"] != previous_numbers[name]["numbers"]:
            path = numbers[name]["path"]
            differences.append("Changed: {} ({})".format(name, path))

    return differences


def get_previous_log_path():
    """Return path to directory with most recent numbers.json, or None if it
    does not exist.

    If no such file exists, this is probably the first run since an import.
    """

    paths = glob(os.path.join(settings.CHECK_NUMBERS_BASE_PATH, "*", "numbers.json"))
    if not paths:
        return None

    return os.path.dirname(sorted(paths)[-1])


def write_numbers(numbers, log_path):
    """Write scraped numbers from this run."""

    with open(os.path.join(log_path, "numbers.json"), "w") as f:
        json.dump(numbers, f, indent=2, sort_keys=True)


def load_previous_numbers(previous_log_path):
    """Load scraped numbers from previous run."""

    with open(os.path.join(previous_log_path, "numbers.json")) as f:
        return json.load(f)
