import csv
import glob
import sys
from django.core.management.base import BaseCommand, CommandError
from frontend.models import Practice


class Command(BaseCommand):
    args = ''
    help = 'Import practice data. '

    def add_arguments(self, parser):
        parser.add_argument('--practice_file')

    def handle(self, *args, **options):
        self.IS_VERBOSE = False
        if options['verbosity'] > 1:
            self.IS_VERBOSE = True

        if options['practice_file']:
            practice_files = [options['practice_file']]
        else:
            practice_files = glob.glob('./data/raw_data/T*ADDR*')
        for f in practice_files:
            self.import_practices(f)

    def _strip_dict(self, row):
        '''
        Strip whitespace from keys and values in dictionary.
        '''
        for k in row:
            if row[k]:
                row[k] = row[k].strip()
            row[k.strip()] = row.pop(k)
        return row

    def import_practices(self, filename):
        if self.IS_VERBOSE:
            print 'Importing practices from %s' % filename
        lines = count = 0
        practices = csv.reader(open(filename, 'rU'))
        for row in practices:
            row = [i.strip() for i in row]
            p, created = Practice.objects.get_or_create(
                code=row[1]
            )
            p.name = row[2]
            p.address1 = row[3]
            p.address2 = row[4]
            p.address3 = row[5]
            p.address4 = row[6]
            p.postcode = row[7]
            p.save()
            lines += 1
            if created:
                count += 1
        if self.IS_VERBOSE:
            print '%s lines read, %s Practice objects created' % (lines, count)
