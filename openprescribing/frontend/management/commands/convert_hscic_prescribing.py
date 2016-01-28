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
            filenames = glob.glob('./data/raw_data/T*PDPI+BNFT.CSV')

        for f in filenames:
            if self.IS_VERBOSE:
                print "--------- Converting %s -----------" % f
            reader = csv.reader(open(f, 'rU'))
            next(reader)
            filename_for_output = self.create_filename_for_output_file(f)
            writer = csv.writer(open(filename_for_output, 'wb'))
            for row in reader:
                print row
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
        chemical_id = self.get_chemical_id(row[3])
        actual_cost = float(row[7])
        quantity = int(row[8])
        if quantity:
            price_per_unit = actual_cost / float(quantity)
        else:
            price_per_unit = 0
        month = row[9]
        formatted_date = '%s-%s-01' % (month[:4], month[4:])
        output = [row[0], row[1], row[2], chemical_id, row[3],
                  row[4], int(row[5]), float(row[6]), float(row[7]),
                  quantity, formatted_date, price_per_unit]
        return output

    def get_chemical_id(self, presentation_id):
        '''
        In most cases the chemical ID for the presentation is a 9-letter
        code, but in a few cases the HSCIC specifies 4-letter codes.
        These are the cases below.
        '''
        first_four = presentation_id[:4]
        if first_four in self.FOUR_LETTER_CHEMICAL_CODES:
            chemical_id = first_four
        else:
            chemical_id = presentation_id[:9]
        return chemical_id

    FOUR_LETTER_CHEMICAL_CODES = [u'2001', u'2002', u'2003', u'2004', u'2005',
                                  u'2006', u'2007', u'2008', u'2009', u'2010',
                                  u'2011', u'2012', u'2013', u'2014', u'2015',
                                  u'2016', u'2017', u'2018', u'2020', u'2101',
                                  u'2102', u'2103', u'2104', u'2105', u'2106',
                                  u'2107', u'2108', u'2109', u'2110', u'2111',
                                  u'2112', u'2113', u'2114', u'2116', u'2117',
                                  u'2118', u'2119', u'2120', u'2121', u'2122',
                                  u'2123', u'2124', u'2125', u'2126', u'2127',
                                  u'2128', u'2129', u'2130', u'2131', u'2132',
                                  u'2133', u'2134', u'2135', u'2136', u'2137',
                                  u'2138', u'2139', u'2140', u'2141', u'2142',
                                  u'2143', u'2144', u'2145', u'2146', u'2202',
                                  u'2205', u'2210', u'2215', u'2220', u'2230',
                                  u'2240', u'2250', u'2260', u'2270', u'2280',
                                  u'2285', u'2290', u'2305', u'2310', u'2315',
                                  u'2320', u'2325', u'2330', u'2335', u'2340',
                                  u'2345', u'2346', u'2350', u'2355', u'2360',
                                  u'2365', u'2370', u'2375', u'2380', u'2385',
                                  u'2390', u'2392', u'2393', u'2394', u'2396',
                                  u'2398', u'2399']
