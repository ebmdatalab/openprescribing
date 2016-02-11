import csv
import sys
from django.core.management.base import BaseCommand, CommandError
from frontend.models import Practice, PCT, SHA


class Command(BaseCommand):
    args = ''
    help = 'Relates practices to CCGs, based on HSCIC data. '
    help += 'Around 20 practices do not have a CCG, only an AT - these are '
    help += 'mostly prison practices.'
    help += 'Also around 100 practices in our data are not found in the '
    help += 'latest version of this file - these are non-active practices.'
    help += "Expects the epraccur.csv file"

    def add_arguments(self, parser):
        parser.add_argument('--filename')

    def handle(self, *args, **options):
        if not options['filename']:
            print 'Please provide a filename'
            sys.exit()

        entries = csv.reader(open('%s' % options['filename'], 'rU'))
        for row in entries:
            try:
                practice = Practice.objects.get(code=row[0])
                try:
                    pco_code = row[14].strip()
                    ccg = PCT.objects.get(code=pco_code)
                    practice.ccg = ccg
                except PCT.DoesNotExist:
                    print 'ccg not found with code', pco_code
                practice.save()
            except Practice.DoesNotExist:
                pass
