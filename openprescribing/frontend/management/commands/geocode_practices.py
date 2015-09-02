import csv
import requests
import sys
import time
from django.core.management.base import BaseCommand, CommandError
from frontend.models import Practice
from common import utils


class Command(BaseCommand):
    args = ''
    help = 'Geocodes all our practices, using the OpenCageData API.'

    def handle(self, *args, **options):
        self.IS_VERBOSE = False
        if options['verbosity'] > 1:
            self.IS_VERBOSE = True

        BASE_URL = 'http://api.opencagedata.com/geocode/v1/json?'
        BASE_URL += '&key=%s' % utils.get_env_setting('OPENCAGEDATA_KEY')
        practices = Practice.objects.all().reverse()
        for practice in practices:
            if practice.location:
                continue
            geom = self.fetch_from_opencage(BASE_URL,
                                            practice.address_pretty())
            if not geom:
                address = practice.address_pretty_minus_firstline()
                geom = self.fetch_from_opencage(BASE_URL, address)
            if geom:
                lat = geom['lat']
                lng = geom['lng']
                practice.location = 'POINT(%s %s)' % (lng, lat)
                practice.save()

    def fetch_from_opencage(self, BASE_URL, address):
        time.sleep(2)
        url = '%s&q=%s' % (BASE_URL, address)
        if self.IS_VERBOSE:
            print url
        geom = None
        resp = requests.get(url)
        data = resp.json()
        if 'rate' in data:
            print data['rate']['remaining'], 'requests remaining'
            if data['rate']['remaining'] == 0:
                print 'No more requests remaining under rate limit'
                sys.exit()
        if 'results' in data:
            if len(data['results']):
                if self.IS_VERBOSE:
                    print len(data['results']), 'results found'
                result = data['results'][0]
                geom = result['geometry']
        return geom
