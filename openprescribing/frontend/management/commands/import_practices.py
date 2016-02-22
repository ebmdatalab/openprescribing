import csv
import glob
from django.core.management.base import BaseCommand, CommandError
from frontend.models import Practice, PCT, SHA


class Command(BaseCommand):
    args = ''
    help = 'Imports practice data either from epraccur.csv, or from HSCIC '
    help += 'address files, depending on options. '

    def add_arguments(self, parser):
        parser.add_argument('--hscic_address')
        parser.add_argument('--epraccur')

    def handle(self, *args, **options):
        self.IS_VERBOSE = False
        if options['verbosity'] > 1:
            self.IS_VERBOSE = True

        if options['epraccur']:
            self.import_practices_from_epraccur(options['epraccur'])
        practice_files = []
        if options['hscic_address']:
            practice_files = [options['hscic_address']]
        else:
            practice_files = glob.glob('./data/raw_data/T*ADDR*')
        for f in practice_files:
            self.import_practices_from_hscic(f)

    def parse_date(self, d):
        return '-'.join([d[:4], d[4:6], d[6:]])

    def _strip_dict(self, row):
        '''
        Strip whitespace from keys and values in dictionary.
        '''
        for k in row:
            if row[k]:
                row[k] = row[k].strip()
            row[k.strip()] = row.pop(k)
        return row

    def import_practices_from_epraccur(self, filename):
        entries = csv.reader(open(filename, 'rU'))
        count = 0
        for row in entries:
            row = [r.strip() for r in row]
            practice, created = Practice.objects.get_or_create(
                code=row[0]
            )

            practice.name = row[1]
            practice.address1 = row[4]
            practice.address2 = row[5]
            practice.address3 = row[6]
            practice.address4 = row[7]
            practice.address5 = row[8]
            practice.postcode = row[9]

            practice.open_date = self.parse_date(row[10])
            if row[11]:
                practice.close_date = self.parse_date(row[11])
            practice.status_code = row[12]

            try:
                pco_code = row[14].strip()
                ccg = PCT.objects.get(code=pco_code)
                practice.ccg = ccg
            except PCT.DoesNotExist:
                print 'ccg not found with code', pco_code

            if row[15]:
                practice.join_provider_date = self.parse_date(row[15])
            if row[16]:
                practice.leave_provider_date = self.parse_date(row[16])

            practice.setting = row[-2]
            practice.save()
            if created:
                count += 1

        if self.IS_VERBOSE:
            print '%s Practice objects created from epraccur' % count

    def import_practices_from_hscic(self, filename):
        if self.IS_VERBOSE:
            print 'Importing practices from %s' % filename
        count = 0
        practices = csv.reader(open(filename, 'rU'))
        for row in practices:
            row = [i.strip() for i in row]
            p, created = Practice.objects.get_or_create(
                code=row[1]
            )
            if created:
                p.name = row[2]
                p.address1 = row[3]
                p.address2 = row[4]
                p.address3 = row[5]
                p.address4 = row[6]
                p.postcode = row[7]
                p.save()
                if created:
                    count += 1

        if self.IS_VERBOSE:
            print '%s Practice objects created from HSCIC' % count
