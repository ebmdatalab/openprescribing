import requests
from basecommand import BaseCommand
from lxml import html
import re
from dateutil.parser import parse
import subprocess
import urlparse


"""The HSCIC data is the source of prescribing data.
"""

PREFIX = 'data/patient_list_size'


class Command(BaseCommand):
    args = ''
    help = ('Fetches all HSCIC data and rewrites filenames to be consistent.'
            'With no arguments, fetches data for every month since Aug 2010')

    def handle(self):
        date, source_url = self.most_recent_data()
        if self.args.verbose:
            print "Getting data for %s-%s" % (date.year, date.month)
        self.get_data(date, source_url)
        if self.args.verbose:
            print "Done"

    def get_data(self, date, source_url):
        target_path = "%s/%s_%s" % (
            PREFIX, date.year, str(date.month).zfill(2))
        self.mkdir_p(target_path)
        target_file = "patient_list_size_new.csv"
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
        if self.args.verbose:
            print 'Runing %s' % cmd
        subprocess.check_call(cmd.split())

    def most_recent_data(self):
        url = ('http://content.digital.nhs.uk'
               '/article/2021/Website-Search?'
               'q=Numbers+of+Patients+Registered+at+a+GP+Practice'
               '&go=Go&area=both')
        page = requests.get(url)
        tree = html.fromstring(page.content)
        first_link_text = tree.xpath(
            '//li[contains(@class, "HSCICProducts")]//a/text()')[0]
        first_link_href = tree.xpath(
            '//li[contains(@class, "HSCICProducts")]//a/@href')[0]
        most_recent_date = re.search(r" - (.*)$", first_link_text).groups()[0]
        o = urlparse.urlparse(first_link_href)
        q = urlparse.parse_qs(o.query)
        page = requests.get(
            "http://content.digital.nhs.uk/article/2021/Website-Search"
            "?productid=%s" % q['productid'][0])
        tree = html.fromstring(page.content)
        first_link = tree.xpath(
            "//a[contains(@href, 'gp-reg-pat-prac-quin-age')]/@href")[0]
        return (parse(most_recent_date),
                "http://content.digital.nhs.uk/%s" % first_link)


if __name__ == '__main__':
    Command().handle()
