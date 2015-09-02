import csv
import sys
from django.core.management.base import BaseCommand, CommandError
from frontend.models import Practice


class Command(BaseCommand):
    args = ''
    help = 'Imports practice prescribing setting.'

    def add_arguments(self, parser):
        parser.add_argument('--filename')

    def handle(self, *args, **options):
        self.IS_VERBOSE = False
        if options['verbosity'] > 1:
            self.IS_VERBOSE = True

        if not options['filename']:
            print 'Please supply a filename'
            sys.exit()

        reader = csv.reader(open(options['filename'], 'rU'))
        codes = []
        for row in reader:
            code = row[0]
            setting = int(row[-2])
            try:
                practice = Practice.objects.get(code=code)
                if practice:
                    practice.setting = setting
                    practice.save()
            except Practice.DoesNotExist:
                pass
