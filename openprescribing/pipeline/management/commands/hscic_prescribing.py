import requests
from lxml import html
import re
from dateutil.parser import parse
import calendar
import subprocess
from zipfile import ZipFile
import os

from django.conf import settings
from django.core.management import BaseCommand


"""The HSCIC data is the source of prescribing data.
"""

PREFIX = os.path.join(settings.PIPELINE_DATA_BASEDIR, 'prescribing')


class Command(BaseCommand):
    args = ''
    help = ('Fetches all HSCIC data and rewrites filenames to be consistent.'
            'With no arguments, fetches data for every month since Aug 2010')

    def add_arguments(self, parser):
        parser.add_argument('--most_recent_date', action='store_true')
        parser.add_argument('--start_date')
        parser.add_argument(
            '--sample',
            action='store_true',
            help="Download a representative sample, useful for development")

    def handle(self, *args, **kwargs):
        self.verbose = (kwargs['verbosity'] > 1)

        if kwargs['sample']:
            date_range = self.sample_date_range()
        else:
            if kwargs['start_date']:
                start_date = parse(kwargs['start_date'])
                end_date = self.most_recent_date()
            elif kwargs['most_recent_date']:
                start_date = self.most_recent_date()
                end_date = start_date
            else:
                start_date = parse("2010/08")
                end_date = self.most_recent_date()
            date_range = self.date_range(start_date, end_date)
        for year, month in date_range:
            if self.verbose:
                print "Getting data for %s-%s" % (year, month)
            target_path = "%s/%s_%s" % (PREFIX, year, str(month).zfill(2))
            self.mkdir_p(target_path)
            try:
                self.get_zipped_version(year, month, target_path)
            except subprocess.CalledProcessError:
                self.get_unzipped_version(year, month, target_path)
            self.extension_to_uppercase(target_path, 'csv')
        if self.verbose:
            print "Done"

    def get_zipped_version(self, year, month, target_path):
        target_file = "%s/%s_%s_hscic.zip" % (target_path, year, month)
        month_name = calendar.month_name[month]
        poss_month_names = [month_name, month_name.lower(),
                            month_name[:3], month_name[:3].lower()]
        for possibility in poss_month_names:
            path = "%s_%s_%s" % (year, str(month).zfill(2),
                                 month_name)
            name = "%s_%s_%s" % (year, str(month).zfill(2),
                                 possibility)
            url = "%s/%s.exe" % (path, name)
            try:
                self.wget_and_return(url, target_file)
                break
            except subprocess.CalledProcessError:
                print "Nothing found at ", url
                next
        z = ZipFile(target_file)
        if len(z.namelist()) == 3:
            z.extractall("%s/%s_%s/" % (PREFIX, year, str(month).zfill(2)))
        else:
            raise "Unexpected file count in archive at %s" % target_file

    def get_unzipped_version(self, year, month, target_path):
        '''
        The HSCIC URLs *usually* end with an uppercase .CSV but not
        always. Try them with the uppercase suffix first, then with
        a lowercase .csv suffix if they fail.
        '''
        individual_files = ['PDPI+BNFT', 'ADDR+BNFT', 'CHEM+SUBS']
        month_filled = str(month).zfill(2)
        date_part = "%s_%s_%s" % (
            year, month_filled, calendar.month_name[month])
        for f in individual_files:
            for date_part_with_case in [date_part, date_part.lower()]:
                basename = "T%s%s%s" % (year, month_filled, f)
                target_file = "%s/%s.CSV" % (target_path, basename)
                for name in ["%s.CSV" % basename, "%s.csv" % basename]:
                    url = "%s/%s" % (date_part_with_case, name)
                    try:
                        self.wget_and_return(url, target_file)
                    except subprocess.CalledProcessError:
                        print "Couldn't get url %s" % url

    def wget_and_return(self, url, target_file):
        '''
        Call wget, raise exception on error
        Does not overwrite existing files.
        '''
        base_url = "http://datagov.ic.nhs.uk/presentation"
        wget_command = 'wget -c -O %s' % target_file
        cmd = '%s %s' % (wget_command, "%s/%s" % (base_url, url))
        if self.verbose:
            print 'Runing %s' % cmd
        subprocess.check_call(cmd.split())

    def construct_url_path(self, year, month, filename, suffix, lowercase):
        '''
        Construct the full URL paths used by the HSCIC.
        Suffix is sometimes CSV and sometimes csv.
        '''
        hscic_prefix = 'http://datagov.ic.nhs.uk/presentation/'
        month_name = self.get_full_month_name(month, lowercase)
        if month < 10:
            month = '0%s' % month
        url_to_fetch = "%s%s_%s_%s" % (hscic_prefix, year, month, month_name)
        url_to_fetch += "/T%s%s%s.%s" % (year, month, filename, suffix)
        return url_to_fetch

    def sample_date_range(self):
        most_recent_date = self.most_recent_date()
        return [[parse(d).year, parse(d).month] for d in [
            "2011/%s" % most_recent_date.month,
            "%s/%s" % (most_recent_date.year - 1, most_recent_date.month),
            "%s/%s" % (most_recent_date.year, most_recent_date.month)]
        ]

    def most_recent_date(self):
        url = ('http://content.digital.nhs.uk'
               '/searchcatalogue?'
               'q=title%3a%22presentation+level+data%22&sort=Most+recent')
        page = requests.get(url)
        tree = html.fromstring(page.content)
        first_link = tree.xpath(
            '//li[@class="item HSCICProducts first"]//a/text()')[0]
        most_recent_date = re.search(r" - (.*)$", first_link).groups()[0]
        return parse(most_recent_date)

    def date_range(self, start, end):
        for year in range(start.year, end.year + 1):
            for month in range(1, 13):
                if year == start.year and month < start.month:
                    continue
                if year == end.year and month > end.month:
                    break
                yield [year, month]

    def extension_to_uppercase(self, path, suffix):
        for name in glob.glob("%s/*.%s" % (path, suffix.lower())):
            os.rename(
                name,
                "%s.%s" % (name[:-(len(suffix)+1)], suffix.upper())
            )

    def mkdir_p(self, path):
        try:
            os.makedirs(path)
        except OSError as exc:  # Python >2.5
            if exc.errno == errno.EEXIST and os.path.isdir(path):
                pass
            else:
                raise
