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
        converted_filenames = []
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
            converted_filenames.append(filename_for_output)
        return converted_filenames

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
        chemical_id = self.get_chemical_id(row[3])
        actual_cost = float(row[7])
        quantity = int(row[8])
        month = row[9]
        formatted_date = '%s-%s-01' % (month[:4], month[4:])
        output = [row[0], row[1], row[2], chemical_id, row[3],
                  row[4], int(row[5]), float(row[7]),
                  quantity, formatted_date]
        return output

    def get_chemical_id(self, presentation_id):
        '''In most cases the chemical ID for the presentation is a 9-letter
        code, but where the chapter starts with '2', the HSCIC
        specifies 4-letter codes.

        '''
        if presentation_id[0] == '2':
            chemical_id = presentation_id[:4]
        else:
            chemical_id = presentation_id[:9]
        return chemical_id
