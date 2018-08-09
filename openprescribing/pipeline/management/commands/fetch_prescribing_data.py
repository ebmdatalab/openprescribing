

from argparse import RawTextHelpFormatter
import datetime
import os
import zipfile

from lxml import html
import requests
from tqdm import tqdm

from django.conf import settings
from django.core.management import BaseCommand, CommandError

from openprescribing.utils import mkdir_p


class Command(BaseCommand):
    # Note that this is mostly-duplicated below, but I can't see a nice way of
    # avoiding that.
    help = '''
This command downloads the prescribing data for a given year and month.  Does
nothing if data already downloaded.  Raises exception if data not found.

The data is on a site that is protected by a captcha.  To download it, you will
need to solve the captcha in your browser.  This will set a cookie in your
browser which you will need to pass to this command.

Specifically, you should:

    * Visit
      https://apps.nhsbsa.nhs.uk/infosystems/data/showDataSelector.do?reportId=124
      in your browser
    * Solve the captcha and click on "Guest Login"
    * Copy the value of the JSESSIONID cookie
      * In Chrome, this can be found in the Application tab of Developer Tools
    * Run `./manage.py fetch_prescribing_data [year] [month] [cookie]`
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
The data is on a site that is protected by a captcha.  To download it, you will
need to solve the captcha in your browser.  This will set a cookie in your
browser which you will need to paste below.

Specifically, you should:

    * Visit https://apps.nhsbsa.nhs.uk/infosystems/data/showDataSelector.do?reportId=124 in your browser
    * Solve the captcha and click on "Guest Login"
    * Copy the value of the JSESSIONID cookie
      * In Chrome, this can be found in the Application tab of Developer Tools
    * Paste this value below:
            '''.strip())

            jsessionid = input()
        else:
            jsessionid = kwargs['jsessionid']

        self.path = os.path.join(settings.PIPELINE_DATA_BASEDIR, 'prescribing')
        self.base_url = 'https://apps.nhsbsa.nhs.uk/infosystems/data/'

        session = requests.Session()
        session.cookies['JSESSIONID'] = jsessionid

        date = datetime.date(kwargs['year'], kwargs['month'], 1)
        year_and_month = date.strftime('%Y_%m')  # eg 2017_01
        datestr = date.strftime('%b, %Y').upper()  # eg JAN, 2017

        if self.already_downloaded(year_and_month):
            print('Already downloaded data for', year_and_month)
            return

        period_id = self.period_id(session, datestr)

        if period_id is None:
            raise CommandError('Could not find data for %s' % year_and_month)

        self.download_csv(session, year_and_month, period_id)

    def already_downloaded(self, year_and_month):
        return os.path.exists(os.path.join(self.path, year_and_month))

    def period_id(self, session, datestr):
        url = self.base_url + 'showDataSelector.do'
        params = {'reportId': '124'}
        rsp = session.get(url, params=params)

        tree = html.fromstring(rsp.content)

        links = tree.xpath('//a[@filtertype="MONTHLY"]')
        for link in links:
            if link.text.strip() == datestr:
                return link.attrib['id']

    def download_csv(self, session, year_and_month, period_id):
        dir_path = os.path.join(self.path, year_and_month)
        zip_path = os.path.join(dir_path, 'download.zip')

        url = self.base_url + 'requestSelectedDownload.do'
        params = {
            'period': period_id,
            'filePath': '',
            'dataView': '255',
            'format': '',
            'periodType': 'MONTHLY',
            'defaultPeriod': '200',
            'defaultFilterType': 'MONTHLY',
            'organisation': '11',
            'dimensionHierarchyId': '1',
            'bnfChapter': '0',
            'defaultReportIdDataSel': '',
            'reportId': '124',
            'action': 'checkForAvailableDownload',
        }

        rsp = session.get(url, params=params)
        request_id = rsp.json()['requestNo']

        mkdir_p(dir_path)

        url = self.base_url + 'downloadAvailableReport.zip'
        params = {
            'requestId': request_id,
        }

        rsp = session.post(url, params=params, stream=True)

        total_size = int(rsp.headers['content-length'])

        progress_bar = tqdm(total=total_size, unit='B', unit_scale=True)

        with open(zip_path, 'wb') as f:
            for block in rsp.iter_content(32 * 1024):
                f.write(block)
                progress_bar.update(len(block))

        with zipfile.ZipFile(zip_path) as zf:
            zf.extractall(dir_path)
