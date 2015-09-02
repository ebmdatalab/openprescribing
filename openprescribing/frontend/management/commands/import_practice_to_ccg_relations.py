import csv
import sys
from django.core.management.base import BaseCommand, CommandError
from frontend.models import Practice, PCT, SHA


class Command(BaseCommand):
    args = ''
    help = 'Relates practices to managing organisations, based on BSA data. '
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
                    pco_code = row[14]
                    ccg = PCT.objects.get(code=pco_code)
                    practice.ccg = ccg
                except PCT.DoesNotExist:
                    print 'ccg not found with code', pco_code
                # try:
                #     area_team = SHA.objects.get(code=row[3])
                #     practice.area_team = area_team
                # except SHA.DoesNotExist:
                #     pass
                    # print 'area team', row[3], 'not found'
                practice.save()
            except Practice.DoesNotExist:
                pass
                # print 'practice not found with code', row[0]

