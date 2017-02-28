import csv
import glob
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    args = ''
    help = 'Converts HSCIC data files into the format needed for our SQL COPY '
    help += 'statement. We use COPY because it is much faster than INSERT.'

    def add_arguments(self, parser):
        parser.add_argument('--filename')

    def handle(self, *args, **options):
        self.IS_VERBOSE = False
        if options['verbosity'] > 1:
            self.IS_VERBOSE = True

        if 'is_test' in options:
            self.IS_TEST = True
        else:
            self.IS_TEST = False

        if options['filename']:
            filenames = [options['filename']]
        else:
            filenames = glob.glob('./data/raw_data/T*PDPI+BNFT.*')

        for f in filenames:
            if self.IS_VERBOSE:
                print "--------- Converting %s -----------" % f
            reader = csv.reader(open(f, 'rU'))
            next(reader)
            filename_for_output = self.create_filename_for_output_file(f)
            writer = csv.writer(open(filename_for_output, 'wb'))
            for row in reader:
                if len(row) == 1:
                    continue
                data = self.format_row_for_sql_copy(row)
                writer.writerow(data)

    def create_filename_for_output_file(self, filename):
        if self.IS_TEST:
            return filename[:-4] + '_test.CSV'
        else:
            return filename[:-4] + '_formatted.CSV'

    def format_row_for_sql_copy(self, row):
        '''
        Transform the data into the format needed for COPY.
        '''
        row = [r.strip() for r in row]
        actual_cost = float(row[7])
        quantity = int(row[8])
        month = row[9]
        formatted_date = '%s-%s-01' % (month[:4], month[4:])
        output = [row[1], row[2], row[3],
                  int(row[5]), actual_cost,
                  quantity, formatted_date]
        return output
