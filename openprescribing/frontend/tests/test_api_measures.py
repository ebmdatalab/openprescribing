import csv
import os
import json
import unittest
from django.core import management
from django.test import TestCase
from common import utils
from frontend.models import SHA, PCT, Chemical, Practice, Prescription


def setUpModule():
    sha = SHA.objects.create(code='Q51')
    pct = PCT.objects.create(code='02Q')
    c = Chemical.objects.create(bnf_code='0403010J0',
                                chem_name='Dosulepin Hydrochloride')
    p1 = Practice.objects.create(code='C84001',
                                 name='LARWOOD SURGERY', setting=4)
    p2 = Practice.objects.create(code='C84024',
                                 name='NEWGATE MEDICAL GROUP', setting=4)
    Practice.objects.create(code='Y00581',
                            name='BASSETLAW DRUG & ALCOHOL SERVICE',
                            setting=4)
    Prescription.objects.create(sha=sha, pct=pct, practice=p1, chemical=c,
                                presentation_code='0403010J0AAAIAI',
                                presentation_name='Dosulepin HCl_Tab 75mg',
                                total_items=34,
                                net_cost=63.79,
                                actual_cost=59.53,
                                quantity=1215,
                                processing_date='2013-09-01',
                                price_per_unit=0.048995884)
    Prescription.objects.create(sha=sha, pct=pct, practice=p1, chemical=c,
                                presentation_code='0403030D0AAAAAA',
                                presentation_name='Citalopram Hydrob_Tab 20mg',
                                total_items=381,
                                net_cost=422.43,
                                actual_cost=395.91,
                                quantity=11480,
                                processing_date='2013-09-01',
                                price_per_unit=0.03448693379790941)
    Prescription.objects.create(sha=sha, pct=pct, practice=p2, chemical=c,
                                presentation_code='0403010J0AAAIAI',
                                presentation_name='Dosulepin HCl_Tab 75mg',
                                total_items=34,
                                net_cost=63.79,
                                actual_cost=59.53,
                                quantity=1215,
                                processing_date='2013-09-01',
                                price_per_unit=0.048995884)
    Prescription.objects.create(sha=sha, pct=pct, practice=p2, chemical=c,
                                presentation_code='0403030E0AAACAC',
                                presentation_name='Fluoxetine HCl_Oral Soln 20mg/5ml',
                                total_items=2,
                                net_cost=12.81,
                                actual_cost=11.86,
                                quantity=210,
                                processing_date='2013-09-01',
                                price_per_unit=0.05647619047619047)
    args = []
    opts = {
        'month': '2013-09-01'
    }
    management.call_command('import_dosulepin', *args, **opts)


def tearDownModule():
    management.call_command('flush', verbosity=0, interactive=False)


class TestAPIMeasureViews(TestCase):

    api_prefix = '/api/1.0'

    def test_api_measure_global(self):
        url = '/api/1.0/measure/?measure=ktt8_dosulepin&format=json'
        response = self.client.get(url, follow=True)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['measure']['name'], 'KTT8 (Dosulepin)')
        self.assertEqual(len(data['data']), 1)
        d = data['data'][0]
        self.assertEqual(d['numerator'], 68)
        self.assertEqual(d['denominator'], 451)
        self.assertEqual("%.4f" % d['calc_value'], '0.1508')
        self.assertEqual("%.4f" % d['practice_10th'], '0.0164')
        self.assertEqual("%.4f" % d['practice_25th'], '0.0410')
        self.assertEqual("%.4f" % d['practice_50th'], '0.0819')
        self.assertEqual("%.4f" % d['practice_75th'], '0.5132')
        self.assertEqual("%.4f" % d['practice_90th'], '0.7719')

    def test_api_measure_by_practice(self):
        url = '/api/1.0/measure_by_practice/'
        url += '?org=C84001&measure=ktt8_dosulepin&format=json'
        response = self.client.get(url, follow=True)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(len(data['data']), 1)
        self.assertEqual(data['data'][0]['numerator'], 34)
        self.assertEqual(data['data'][0]['denominator'], 415)
        calc_value = data['data'][0]['calc_value']
        self.assertEqual("%.4f" % calc_value, '0.0819')
