import datetime
import os
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    args = ''
    help = 'Fetches all HSCIC data and rewrites filenames to be consistent'

    def add_arguments(self, parser):
        parser.add_argument('--start_date')

    def handle(self, *args, **options):
        if options['start_date']:
            dates = options['start_date'].split('-')
            START_YEAR = int(dates[0])
            START_MONTH = int(dates[1])
        else:
            START_YEAR = 2010
            START_MONTH = 8
        now = datetime.datetime.now()
        END_YEAR = now.year
        END_MONTH = now.month
        for year in range(START_YEAR, END_YEAR + 1):
            for month in range(1, 13):
                if year == START_YEAR and month < START_MONTH:
                    continue
                if year == END_YEAR and month > END_MONTH:
                    continue
                self.call_wget_and_retry_if_needed(year, month, "PDPI+BNFT")
                self.call_wget_and_retry_if_needed(year, month, "ADDR+BNFT")
                self.call_wget_and_retry_if_needed(year, month, "CHEM+SUBS")

        self.give_files_consistent_suffix()
        num_files = self.check_number_of_files()
        num_files_expected = self.files_expected(START_YEAR, START_MONTH,
                                                 END_YEAR, END_MONTH)
        if num_files != num_files_expected:
            print 'Fewer files returned than expected, only', num_files

    def call_wget_and_retry_if_needed(self, year, month, filename):
        '''
        The HSCIC URLs *usually* end with an uppercase .CSV but not
        always. Try them with the uppercase suffix first, then with
        a lowercase .csv suffix if they fail.
        '''
        return_code = self.wget_and_return(year, month, filename, 'CSV')
        if return_code:
            print 'File for %s/%s not downloaded' % (year, month)
            print 'Trying lowercase suffix...'
            return_code = self.wget_and_return(year, month, filename, 'csv')
            if return_code:
                print 'File for %s/%s not downloaded' % (year, month)
                print 'Trying lowercase month name...'
                return_code = self.wget_and_return(year, month, filename,
                                                   'csv', True)
                if return_code:
                    print 'Failed to download file for %s/%s!' % (year, month)
                    print 'Filename that failed: ', filename

    def wget_and_return(self, year, month, filename, suffix, lowercase=False):
        '''
        Call wget, pass back the return code (will be 0 if successful).
        Does not overwrite existing files.
        '''
        wget_command = 'wget -N -P data/raw_data'
        url_to_fetch = self.construct_url_path(year, month, filename, suffix,
                                               lowercase)
        return os.system('%s %s' % (wget_command, url_to_fetch))

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

    def get_full_month_name(self, month, is_lowercase):
        '''
        Get the readable month name used in HSCIC files from the month number.
        '''
        month_name = datetime.date(1900, month, 1).strftime('%B')
        if is_lowercase:
            month_name = month_name.lower()
        return month_name

    def give_files_consistent_suffix(self):
        '''
        Move all .csv files to .CSV, for consistency.
        '''
        os.system('cd data/raw_data')
        cmd = 'for file in *.csv; '
        cmd += 'do mv "$file" "`basename $file .csv`.CSV"; done'
        os.system(cmd)

    def check_number_of_files(self, number_expected):
        cmd = 'ls *.CSV | wc -l'
        num_files = os.system(cmd)
        return num_files, number_expected

    def files_expected(START_YEAR, START_MONTH, END_YEAR, END_MONTH):
        return (END_YEAR - START_YEAR) * 12 + (END_MONTH - START_MONTH)
