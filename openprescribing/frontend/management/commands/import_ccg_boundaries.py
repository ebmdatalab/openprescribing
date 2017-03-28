import sys
from django.core.management.base import BaseCommand
from django.contrib.gis.utils import LayerMapping
from frontend.models import PCT


class Command(BaseCommand):
    args = ''
    help = 'Imports CCG boundaries from mapinfo. Note that you should '
    help += 'run this BEFORE importing CCG names, as this creates new '
    help += 'records in the database rather than updating existing ones.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--filename',
            help='Should point to a filename like `CCG_BSC_Apr2015.TAB`'
        )

    def handle(self, *args, **options):

        if 'filename' not in options:
            print 'Please supply a KML filename'
            sys.exit

        layer_mapping = {
            'code': 'CCGcode',
            'boundary': 'Unknown'
        }
        lm = LayerMapping(PCT, options['filename'],
                          layer_mapping, transform=True)
        lm.save(strict=True)
