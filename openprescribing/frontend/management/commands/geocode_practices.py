import csv
import requests
from django.core.management.base import BaseCommand, CommandError
from django.contrib.gis.gdal import SpatialReference, CoordTransform
from django.contrib.gis.geos import Point
from frontend.models import Practice
from common import utils


class Command(BaseCommand):
    args = ''
    help = 'Add eastings and northings to practices, '
    help += ' from the HSCIC gridall.csv file. '

    def add_arguments(self, parser):
        parser.add_argument('--filename')

    def handle(self, *args, **options):
        '''
        Import practice eastings and northings, from HSCIC data.
        '''
        if not options['filename']:
            print 'Please supply a filename'
        else:
            self.IS_VERBOSE = False
            if options['verbosity'] > 1:
                self.IS_VERBOSE = True

            gridall = csv.reader(open(options['filename'], 'rU'))
            postcodes = {}
            for row in gridall:
                postcode = row[1].replace(' ', '').strip()
                postcodes[postcode] = [row[36], row[37]]

            wgs84 = SpatialReference(4326)
            bng = SpatialReference(27700)
            trans = CoordTransform(bng, wgs84)

            practices = Practice.objects.all().reverse()
            for practice in practices:
                practice.location = None
                postcode = practice.postcode.replace(' ', '').strip()
                if postcode in postcodes:
                    lng = postcodes[postcode][0]
                    lat = postcodes[postcode][1]
                    if lng and lat:
                        pnt = Point(int(lng), int(lat), srid=27700)
                        pnt.transform(trans)
                        practice.location = pnt
                practice.save()
