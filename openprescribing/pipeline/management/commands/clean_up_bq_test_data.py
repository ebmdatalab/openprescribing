import os
from django.core.management import BaseCommand, CommandError
from gcutils.bigquery import Client


class Command(BaseCommand):
    help = 'Removes any datasets whose tables have all expired'

    def handle(self, *args, **kwargs):
        if os.environ['DJANGO_SETTINGS_MODULE'] != \
                'openprescribing.settings.test':
            raise CommandError('Command must run with test settings')

        gcbq_client = Client().gcbq_client

        for dataset in gcbq_client.list_datasets():
            tables = list(dataset.list_tables())
            if len(tables) == 0:
                dataset.delete()
