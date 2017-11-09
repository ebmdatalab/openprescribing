import csv
import sys
from django.core.management.base import BaseCommand
from frontend.models import PCT


class Command(BaseCommand):
    args = ''
    help = 'Imports CCG/PCT names and details, and their relationship '
    help += 'to practices, from HSCIC organisational data. '
    help += 'You should import CCG boundaries BEFORE running this.'

    filenames = ['ccg']

    def add_arguments(self, parser):
        for f in self.filenames:
            parser.add_argument('--' + f)

    def handle(self, *args, **options):
        for f in self.filenames:
            if f not in options:
                print 'Please supply a filename option: ', f
                sys.exit

        ccgs = csv.reader(open(options['ccg'], 'rU'))
        for row in ccgs:
            row = [r.strip() for r in row]
            ccg, created = PCT.objects.get_or_create(
                code=row[0]
            )
            ccg.name = row[1]
            ccg.address = ', '.join([r for r in row[4:9] if r])
            ccg.postcode = row[9]
            od = row[10]
            ccg.open_date = od[:4] + '-' + od[4:6] + '-' + od[-2:]
            cd = row[11]
            if cd:
                ccg.close_date = cd[:4] + '-' + cd[4:6] + '-' + cd[-2:]
            if row[13] == 'C':
                ccg.org_type = 'CCG'
            ccg.save()
