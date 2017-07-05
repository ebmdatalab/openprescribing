from django.core.management import BaseCommand

from ...runner import run_all


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('run_id', nargs='?')

    def handle(self, *args, **kwargs):
        run_all(kwargs['run_id'])
