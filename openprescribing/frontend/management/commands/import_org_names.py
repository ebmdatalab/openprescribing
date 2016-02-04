import csv
import sys
from django.core.management.base import BaseCommand, CommandError
from frontend.models import PCT, SHA


class Command(BaseCommand):
    args = ''
    help = 'Imports CCG/PCT names and details. Imports AT names and '
    help += 'maps ATs to CCGs.'
    help += 'You should import CCG boundaries BEFORE running this.'

    filenames = ['area_team', 'ccg', 'area_team_to_ccg']

    def add_arguments(self, parser):
        for f in self.filenames:
            parser.add_argument('--' + f)

    def handle(self, *args, **options):
        for f in self.filenames:
            if f not in options:
                print 'Please supply a filename option: ', f
                sys.exit

        area_teams = csv.DictReader(open(options['area_team'], 'rU'))
        for row in area_teams:
            area_team, created = SHA.objects.get_or_create(code=row['hscic_code'])
            area_team.ons_code = row['ons_code']
            area_team.name = row['name']
            area_team.save()

        ccgs = csv.DictReader(open(options['ccg'], 'rU'))
        for row in ccgs:
            ccg, created = PCT.objects.get_or_create(
                code=row['CCG13CDH']
            )
            ccg.ons_code = row['CCG13CD']
            ccg.name = row['CCG13NM'].decode('windows-1252').encode('utf8')
            ccg.org_type = 'CCG'
            ccg.save()

        ccgs = csv.DictReader(open(options['area_team_to_ccg'], 'rU'))
        for row in ccgs:
            ccg = PCT.objects.get(ons_code=row['CCG13CD'])
            area_team = SHA.objects.get(ons_code=row['NHSAT13CD'])
            ccg.managing_group = area_team
            ccg.save()
