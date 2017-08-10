from argparse import RawTextHelpFormatter
import datetime
import os
import re
import zipfile

from lxml import html
import requests
from tqdm import tqdm

from django.conf import settings
from django.core.management import BaseCommand

from openprescribing.utils import mkdir_p


class Command(BaseCommand):
    help = '''
This command downloads the latest prescribing data.

It downloads any compressed CSV files that have a date that is later than the
newest file that has already been downloaded.

The files are on a site that is protected by a captcha.  To download the files,
you will need to solve the captcha in your browser.  This will set a cookie in
your browser which you will need to pass to this command.

Specifically, you should:

    * Visit
      https://apps.nhsbsa.nhs.uk/infosystems/data/showDataSelector.do?reportId=124
      in your browser
    * Solve the captcha and click on "Guest Login"
    * Copy the value of the JSESSIONID cookie
      * In Chrome, this can be found in the Application tab of Developer Tools
    * Run `./manage.py fetch_prescribing_data [cookie]`
    '''.strip()

    def create_parser(self, *args, **kwargs):
        parser = super(Command, self).create_parser(*args, **kwargs)
        parser.formatter_class = RawTextHelpFormatter
        return parser

    def add_arguments(self, parser):
        parser.add_argument('jsessionid')

    def handle(self, *args, **kwargs):
        self.path = os.path.join(settings.PIPELINE_DATA_BASEDIR, 'prescribing')
        self.base_url = 'https://apps.nhsbsa.nhs.uk/infosystems/data/'

        session = requests.Session()
        session.cookies['JSESSIONID'] = kwargs['jsessionid']

        for year_and_month, period_id in self.new_download_metadata(session):
            self.download_csv(session, year_and_month, period_id)

    def new_download_metadata(self, session):
        paths = os.listdir(self.path)
        last_downloaded_year_and_month = [
            path for path in paths
            if re.match('^\d{4}_\d{2}$', path)
        ][-1]

        url = self.base_url + 'showDataSelector.do'
        params = {'reportId': '124'}
        rsp = session.get(url, params=params)

        tree = html.fromstring(rsp.content)

        links = tree.xpath('//a[@filtertype="MONTHLY"]')
        for link in links:
            date = datetime.datetime.strptime(link.text.strip(), '%b, %Y')
            year_and_month = date.strftime('%Y_%m')
            if year_and_month > last_downloaded_year_and_month:
                period_id = link.attrib['id']
                yield year_and_month, period_id

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

        with open('download.zip', 'wb') as f:
            for block in rsp.iter_content(32 * 1024),
                f.write(block)
                progress_bar.update(len(block))

        with zipfile.ZipFile(zip_path) as zf:
            zf.extractall(dir_path)
