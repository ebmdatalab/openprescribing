from django.core.management import BaseCommand

from ...runner import run_all


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('year', type=int)
        parser.add_argument('month', type=int)

    def handle(self, *args, **kwargs):
        run_all(kwargs['year'], kwargs['month'])
