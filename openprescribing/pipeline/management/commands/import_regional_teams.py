import csv
from django.core.management import BaseCommand
from frontend.models import PCT, RegionalTeam


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('--filename')

    def handle(self, *args, **kwargs):
        with open(kwargs['filename']) as f:
            for row in csv.reader(f):
                if row[0][0] != 'Y':
                    continue

                team, _ = RegionalTeam.objects.get_or_create(code=row[0])
                team.name = row[1]
                team.address = ', '.join([r for r in row[4:8] if r])
                team.postcode = row[9]
                od = row[10]
                team.open_date = od[:4] + '-' + od[4:6] + '-' + od[-2:]
                cd = row[11]
                if cd:
                    team.close_date = cd[:4] + '-' + cd[4:6] + '-' + cd[-2:]
                team.save()
