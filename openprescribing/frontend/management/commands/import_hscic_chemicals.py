from __future__ import print_function

import csv
import glob
import sys
from django.core.management.base import BaseCommand
from frontend.models import Chemical


class Command(BaseCommand):
    args = ''
    help = 'Import any chemicals not present in the BNF codes list. '
    help += 'This helps us avoid integrity errors when importing the data. '
    help += 'You should have run import_bnf_codes before running this.'

    def add_arguments(self, parser):
        parser.add_argument('--chem_file')

    def handle(self, *args, **options):
        self.IS_VERBOSE = False
        if options['verbosity'] > 1:
            self.IS_VERBOSE = True

        self.import_missing_chemicals()

        if options['chem_file']:
            chem_files = [options['chem_file']]
        else:
            chem_files = glob.glob('./data/raw_data/T*CHEM*')
        for f in chem_files:
            self.import_chemicals(f)

    def _strip_dict(self, row):
        '''
        Strip whitespace from keys and values in dictionary.
        '''
        for k in row:
            if row[k]:
                row[k] = row[k].strip()
            row[k.strip()] = row.pop(k)
        return row

    def import_chemicals(self, filename):
        if self.IS_VERBOSE:
            print('Importing Chemicals from %s' % filename)
        lines = count = 0
        chemicals = csv.DictReader(open(filename, 'rU'))
        for row in chemicals:
            row = self._strip_dict(row)
            bnf_code = row['CHEM SUB']
            if '+' in bnf_code:
                print('ERROR in BNF code format:', bnf_code)
                print('In file:', filename)
                sys.exit()
            c, created = Chemical.objects.get_or_create(
                bnf_code=bnf_code
            )
            c.chem_name = row['NAME']
            c.save()
            lines += 1
            count += created
        if self.IS_VERBOSE:
            print('%s lines read, %s Chemical objects created' % (lines, count))

    def import_missing_chemicals(self):
        '''
        Import chemicals that are in the 2010/11 prescription data file,
        but are missing from the related chemicals file.
        This prevents integrity errors when creating foreign keys.
        This is a temporary fix until the HSCIC fix this problem.
        '''
        if self.IS_VERBOSE:
            print('Importing missing chemicals')
        missing_chemicals = ['0410000AA', '0410000AB', '0410000A0',
                             '0410000D0', '0410000P0', '0410000H0',
                             '0410000M0', '0410000N0', '0410000Q0',
                             '0410000AC', '0410000L0', '0311010A0']
        for chem_id in missing_chemicals:
            try:
                chem = Chemical.objects.get(bnf_code=chem_id)
            except Chemical.DoesNotExist:
                chem, created = Chemical.objects.get_or_create(
                    bnf_code=chem_id,
                    chem_name='Unknown'
                )
