import os
import unittest

from django.core.management import BaseCommand


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('last_imported')

    def handle(self, *args, **kwargs):
        os.environ['LAST_IMPORTED'] = kwargs['last_imported']
        try:
            # The value of argv is not important
            unittest.main('pipeline.smoketests', argv=['smoketests'])
        except SystemExit:
            pass
