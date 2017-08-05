import requests
from lxml import html
import datetime
import subprocess
import urlparse
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

        source_url = self.url_for_date(date)

        if source_url is None:
            raise CommandError('Could not find any data for %s' % datestamp)

        target_dir = os.path.join(
            settings.PIPELINE_DATA_BASEDIR,
            'patient_list_size',
            datestamp,
        )

        target_file = os.path.join(target_dir, 'patient_list_size_new.csv')

        mkdir_p(target_dir)

        if self.verbose:
            print 'Getting data for {}'.format(datestamp)

        self.get_data(target_file, source_url)

        if self.verbose:
            print "Done"

    def get_data(self, target_file, source_url):
        try:
            self.wget_and_return(source_url, target_file)
        except subprocess.CalledProcessError:
            print "Couldn't get url %s" % source_url

    def wget_and_return(self, url, target_file):
        '''
        Call wget, raise exception on error
        Does not overwrite existing files.
        '''
        wget_command = 'wget -c -O %s' % target_file
        cmd = '%s %s' % (wget_command, url)
        if self.verbose:
            print 'Runing %s' % cmd
        subprocess.check_call(cmd.split())

    def url_for_date(self, date):
        datestr1 = date.strftime('%B %Y')  # eg January 2017
        datestr2 = date.strftime('%b %Y')  # eg Jan 2017

        url = ('http://content.digital.nhs.uk'
               '/article/2021/Website-Search?'
               'q=Numbers+of+Patients+Registered+at+a+GP+Practice'
               '&go=Go&area=both')
        rsp = requests.get(url)
        tree = html.fromstring(rsp.content)

        links = tree.xpath('//li[contains(@class, "HSCICProducts")]//a')

        for link in links:
            title = link.text
            if datestr1 in title or datestr2 in title:
                href = link.attrib['href']
                break
        else:
            return

        parsed_url = urlparse.urlparse(href)
        params = urlparse.parse_qs(parsed_url.query)
        rsp = requests.get(
            "http://content.digital.nhs.uk/article/2021/Website-Search"
            "?productid=%s" % params['productid'][0])
        tree = html.fromstring(rsp.content)
        href = tree.xpath(
            "//a[contains(@href, 'gp-reg-pat-prac-quin-age')]/@href")[0]
        return "http://content.digital.nhs.uk/%s" % href
