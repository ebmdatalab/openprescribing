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

        datasets = list(gcbq_client.list_datasets())

        for dataset_list_item in datasets:
            dataset_ref = dataset_list_item.reference
            tables = list(gcbq_client.list_tables(dataset_ref))
            if len(tables) == 0:
                gcbq_client.delete_dataset(dataset_ref)
