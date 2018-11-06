import csv
from django.core.management import BaseCommand
from frontend.models import PCT, STP


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('--filename')

    def handle(self, *args, **kwargs):
        with open(kwargs['filename']) as f:
            for row in csv.DictReader(f):
                stp, _ = STP.objects.get_or_create(ons_code=row['STP18CD'])
                stp.name = row['STP18NM']
                stp.save()

                ccg = PCT.objects.get(code=row['CCG18CDH'])
                ccg.stp = stp
                ccg.save()
