import csv
from django.core.management import BaseCommand
from django.db import transaction
from frontend.models import STP


class Command(BaseCommand):
    help = """
    This is a one-off command to import ICB names from the eother_namechanges.csv file
    at https://digital.nhs.uk/services/organisation-data-service/integrated-care-boards.
    """

    def add_arguments(self, parser):
        parser.add_argument("path")

    @transaction.atomic
    def handle(self, path, **kwargs):
        with open(path) as f:
            for row in csv.reader(f):
                STP.objects.filter(code=row[0]).update(name=row[1])
