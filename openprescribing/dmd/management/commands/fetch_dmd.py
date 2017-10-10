from argparse import RawTextHelpFormatter
import datetime
import os
import re
import zipfile

from lxml import html
import requests
from tqdm import tqdm

from django.conf import settings
from django.core.management import BaseCommand, CommandError

from openprescribing.utils import mkdir_p


class Command(BaseCommand):
    help = '''
This command downloads the first dm+d data for a given year and month.

It does nothing if the data is already downloaded, and raises an exception if
no data is found.

The files are on a site that requires you to log in.  To download the files,
you will need to visit the site in your browser and log in.  This will set a
cookie in your browser which you will need to pass to this command.

Specifically, you should:

    * Visit
        https://isd.digital.nhs.uk/trud3/user/authenticated/group/0/pack/6/subpack/24/releases
      in your browser
    * Sign up or log in
    * Copy the value of the JSESSIONID cookie
      * In Chrome, this can be found in the Application tab of Developer Tools
    * Run `./manage.py fetch_dmd [year] [month] --jsessionid [cookie]`
    '''.strip()

    def create_parser(self, *args, **kwargs):
        parser = super(Command, self).create_parser(*args, **kwargs)
        parser.formatter_class = RawTextHelpFormatter
        return parser

    def add_arguments(self, parser):
        parser.add_argument('year', type=int)
        parser.add_argument('month', type=int)
        parser.add_argument('--jsessionid')

    def handle(self, *args, **kwargs):
        if kwargs['jsessionid'] is None:
            # Note that this is mostly-duplicated above, but I can't see a nice
            # way of avoiding this.
            print('''
The files are on a site that requires you to log in.  To download the files,
you will need to visit the site in your browser and log in.  This will set a
cookie in your browser which you will need to pass to this command.

Specifically, you should:

    * Visit
        https://isd.digital.nhs.uk/trud3/user/authenticated/group/0/pack/6/subpack/24/releases
      in your browser
    * Sign up or log in
    * Copy the value of the JSESSIONID cookie
      * In Chrome, this can be found in the Application tab of Developer Tools
    * Paste this value below:
            ''').strip()

            jsessionid = raw_input()
        else:
            jsessionid = kwargs['jsessionid']

        year = kwargs['year']
        month = kwargs['month']

        year_and_month = datetime.date(year, month, 1).strftime('%Y_%m')
        dir_path = os.path.join(settings.PIPELINE_DATA_BASEDIR, 'dmd', year_and_month)
        zip_path = os.path.join(dir_path, 'download.zip')

        if os.path.exists(dir_path):
            print('Data already downloaded for', year_and_month)
            return

        mkdir_p(dir_path)

        session = requests.Session()
        session.cookies['JSESSIONID'] = jsessionid


        base_url = 'https://isd.digital.nhs.uk/'

        rsp = session.get(base_url + 'trud3/user/authenticated/group/0/pack/6/subpack/24/releases')

        tree = html.fromstring(rsp.content)

        divs = tree.find_class('release subscribed')

        div_dates = [extract_date(div) for div in divs]
        assert div_dates == sorted(div_dates, reverse=True)

        divs_for_month = []
        for div in divs:
            date = extract_date(div)
            if date.year == year and date.month == month:
                divs_for_month.append(div)

        if not divs_for_month:
            raise CommandError

        div = divs_for_month[-1]
        href = div.find_class('download-release')[0].attrib['href']

        rsp = session.get(base_url + href, stream=True)
        
        with open(zip_path, 'wb') as f:
            for block in rsp.iter_content(32 * 1024):
                f.write(block)

        with zipfile.ZipFile(zip_path) as zf:
            zf.extractall(dir_path)


def extract_date(div):
    return datetime.datetime.strptime(
        div.find('p').text.strip().splitlines()[1].strip(),
        '%A, %d %B %Y'
    )

