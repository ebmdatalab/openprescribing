import requests
from lxml import html
import datetime
import subprocess
import os

from django.conf import settings
from django.core.management import BaseCommand, CommandError

from openprescribing.utils import mkdir_p


class Command(BaseCommand):
    help = '''
    Fetches HSCIC list size data for given year and month.  Does nothing if
    data already downloaded.  Raises exception if data not found.
    '''

    def add_arguments(self, parser):
        parser.add_argument('year', type=int)
        parser.add_argument('month', type=int)

    def handle(self, *args, **kwargs):
        self.verbose = (kwargs['verbosity'] > 1)

        date = datetime.date(kwargs['year'], kwargs['month'], 1)
        datestamp = date.strftime('%Y_%m')

        url = date.strftime('https://digital.nhs.uk/data-and-information/publications/statistical/patients-registered-at-a-gp-practice/%B-%Y').lower()

        rsp = requests.get(url)

        if rsp.status_code != 200:
            raise CommandError('Could not find any data for %s' % datestamp)

        filename = date.strftime('gp-reg-pat-prac-quin-age-%b-%y').lower()
        tree = html.fromstring(rsp.content)
        source_url = tree.xpath(
            "//a[contains(@href, '{}')]/@href".format(filename))[0]

        target_dir = os.path.join(
            settings.PIPELINE_DATA_BASEDIR,
            'patient_list_size',
            datestamp,
        )

        target_file = os.path.join(target_dir, 'patient_list_size_new.csv')

        mkdir_p(target_dir)

        if self.verbose:
            print('Getting data for {}'.format(datestamp))

        self.curl_and_return(source_url, target_file)

        if self.verbose:
            print("Done")

    def curl_and_return(self, url, target_file):
        '''
        Call curl, raise exception on error
        '''
        cmd = 'curl {} -o {}'.format(url, target_file)
        if self.verbose:
            print('Runing %s' % cmd)
        subprocess.check_call(cmd.split())
