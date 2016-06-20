import csv
import sys
from django.core.management.base import BaseCommand, CommandError
from django.contrib.gis.gdal import DataSource
from django.contrib.gis.utils import LayerMapping
from frontend.models import PCT


class Command(BaseCommand):
    args = ''
    help = 'Imports CCG boundaries from KML. Note that you should '
    help += 'run this BEFORE importing CCG names, as this creates new '
    help += 'records in the database rather than updating existing ones.'

    def add_arguments(self, parser):
        parser.add_argument('--filename')

    def handle(self, *args, **options):

        if 'filename' not in options:
            print 'Please supply a KML filename'
            sys.exit

        ds = DataSource(options['filename'])
        layer_mapping = {
            'code': 'Name',
            'boundary': 'Unknown'
        }
        lm = LayerMapping(PCT, options['filename'],
                          layer_mapping, transform=False)  # , unique='code')
        lm.save(strict=True)
