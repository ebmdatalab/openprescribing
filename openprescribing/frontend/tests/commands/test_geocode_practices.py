import os
import unittest
from django.core.management import call_command
from django.test import TestCase
from frontend.models import Practice


def setUpModule():
        Practice.objects.create(code='N84014',
                                name='AINSDALE VILLAGE SURGERY',
                                address1='THE SURGERY',
                                address2='2 LEAMINGTON RD AINSDALE',
                                address3='SOUTHPORT',
                                address4='MERSEYSIDE',
                                postcode='PR8 3LB')
        Practice.objects.create(code='G82650',
                                name='MOCKETTS WOOD SURGERY',
                                address1="THE MOCKETT'S WOOD SURG.",
                                address2='HOPEVILLE AVE ST PETERSY',
                                address3='BROADSTAIRS',
                                address4='KENT',
                                postcode='CT10 2TR')


def tearDownModule():
    call_command('flush', verbosity=0, interactive=False)


class CommandsTestCase(TestCase):

    @unittest.skipIf("TRAVIS" in os.environ and os.environ["TRAVIS"],
                     "Skipping this test on Travis CI.")
    @unittest.skipIf("OPENCAGEDATA_KEY" not in os.environ,
                     "Skipping this test because OPENCAGEDATA_KEY not set.")
    def test_import_practice_geocoding(self):

        args = []
        opts = {}
        call_command('geocode_practices', *args, **opts)

        practice = Practice.objects.get(code='N84014')
        loc = practice.location
        self.assertEqual(loc.x, -3.03576042372)
        self.assertEqual(loc.y, 53.600254095)

        practice = Practice.objects.get(code='G82650')
        loc = practice.location
        self.assertEqual(loc.x, 1.41944991072)
        self.assertEqual(loc.y, 51.3659731963)
