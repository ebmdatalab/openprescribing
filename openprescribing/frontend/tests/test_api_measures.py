import csv
import os
import json
import unittest
from django.core import management
from django.test import TestCase
from common import utils
from frontend.models import SHA, PCT, Chemical, Practice


def setUpModule():
        SHA.objects.create(code='Q51')
        PCT.objects.create(code='02Q')
        Chemical.objects.create(bnf_code='0212000AA',
                                    chem_name='Rosuvastatin Calcium')
        Chemical.objects.create(bnf_code='0212000B0',
                                    chem_name='Atorvastatin')
        Practice.objects.create(code='C84001',
                                name='LARWOOD SURGERY', setting=4)
        Practice.objects.create(code='C84024',
                                name='NEWGATE MEDICAL GROUP', setting=4)
        Practice.objects.create(code='B82005',
                                name='PRIORY MEDICAL GROUP', setting=4,
                                open_date='2015-01-01')
        Practice.objects.create(code='B82010',
                                name='RIPON SPA SURGERY', setting=4)
        Practice.objects.create(code='A85017',
                                name='BEWICK ROAD SURGERY', setting=4)
        Practice.objects.create(code='A86030',
                                name='BETTS AVENUE MEDICAL GROUP', setting=4)
        # Ensure we only include open practices in our calculations.
        Practice.objects.create(code='B82008',
                                name='NORTH HOUSE SURGERY', setting=4,
                                open_date='2010-04-01',
                                close_date='2012-01-01')
        # Ensure we only include standard practices in our calculations.
        Practice.objects.create(code='Y00581',
                                name='BASSETLAW DRUG & ALCOHOL SERVICE',
                                setting=1)

        args = []
        db_name = 'test_' + utils.get_env_setting('DB_NAME')
        db_user = utils.get_env_setting('DB_USER')
        db_pass = utils.get_env_setting('DB_PASS')
        test_file = 'frontend/tests/fixtures/commands/'
        test_file += 'T201509PDPI+BNFT_formatted.CSV'
        new_opts = {
            'db_name': db_name,
            'db_user': db_user,
            'db_pass': db_pass,
            'filename': test_file
        }
        management.call_command('import_hscic_prescribing', *args, **new_opts)

        month = '2015-09-01'
        measure_id = 'rosuvastatin'
        args = []
        opts = {
            'month': month,
            'measure': measure_id
        }
        management.call_command('import_measures', *args, **opts)

def tearDownModule():
    management.call_command('flush', verbosity=0, interactive=False)

class TestAPIMeasureViews(TestCase):

    api_prefix = '/api/1.0'

    def test_api_measure_global(self):
        url = '/api/1.0/measure/?measure=rosuvastatin&format=json'
        response = self.client.get(url, follow=True)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['measures'][0]['name'], 'Rosuvastatin vs. Atorvastatin')
        self.assertEqual(len(data['measures'][0]['data']), 1)
        d = data['measures'][0]['data'][0]
        self.assertEqual(d['numerator'], 82000)
        self.assertEqual(d['denominator'], 143000)
        self.assertEqual("%.4f" % d['calc_value'], '0.5734')
        self.assertEqual("%.4f" % d['practice_10th'], '0.0364')
        self.assertEqual("%.4f" % d['practice_25th'], '0.0909')
        self.assertEqual("%.4f" % d['practice_50th'], '0.3333')
        self.assertEqual("%.4f" % d['practice_75th'], '0.7000')
        self.assertEqual("%.4f" % d['practice_90th'], '0.8800')
        self.assertEqual("%.2f" % d['cost_saving_10th'], '69152.73')
        self.assertEqual("%.2f" % d['cost_saving_25th'], '62181.82')
        self.assertEqual("%.2f" % d['cost_saving_50th'], '33600.00')
        self.assertEqual("%.2f" % d['cost_saving_75th'], '270.00')
        self.assertEqual("%.2f" % d['cost_saving_90th'], '108.00')

    def test_api_all_measures_global(self):
        url = '/api/1.0/measure/?format=json'
        response = self.client.get(url, follow=True)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(len(data['measures'][0]['data']), 1)
        d = data['measures'][0]['data'][0]
        self.assertEqual(d['numerator'], 82000)
        self.assertEqual(d['denominator'], 143000)
        self.assertEqual("%.4f" % d['calc_value'], '0.5734')

    def test_api_measure_by_practice(self):
        url = '/api/1.0/measure_by_practice/'
        url += '?org=C84001&measure=rosuvastatin&format=json'
        response = self.client.get(url, follow=True)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(len(data['measures'][0]['data']), 1)
        d = data['measures'][0]['data'][0]
        self.assertEqual(d['numerator'], 1000)
        self.assertEqual(d['denominator'], 11000)
        self.assertEqual(d['percentile'], 25)
        self.assertEqual("%.4f" % d['calc_value'], '0.0909')
        self.assertEqual("%.2f" % d['cost_saving_10th'], '540.00')
        self.assertEqual("%.2f" % d['cost_saving_25th'], '0.00')
        self.assertEqual("%.2f" % d['cost_saving_50th'], '-2400.00')
        self.assertEqual("%.2f" % d['cost_saving_75th'], '-6030.00')
        self.assertEqual("%.2f" % d['cost_saving_90th'], '-7812.00')

        # Practice with only Rosuva prescribing.
        url = '/api/1.0/measure_by_practice/'
        url += '?org=A85017&measure=rosuvastatin&format=json'
        response = self.client.get(url, follow=True)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        d = data['measures'][0]['data'][0]
        self.assertEqual(d['numerator'], 1000)
        self.assertEqual(d['denominator'], 1000)
        self.assertEqual(d['percentile'], 100)
        self.assertEqual(d['calc_value'], 1)
        self.assertEqual("%.2f" % d['cost_saving_10th'], '867.27')

        # Practice with only Atorva prescribing.
        url = '/api/1.0/measure_by_practice/'
        url += '?org=A86030&measure=rosuvastatin&format=json'
        response = self.client.get(url, follow=True)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(len(data['measures'][0]['data']), 1)
        d = data['measures'][0]['data'][0]
        self.assertEqual(d['numerator'], 0)
        self.assertEqual(d['denominator'], 1000)
        self.assertEqual(d['percentile'], 0)
        self.assertEqual(d['calc_value'], 0)
        self.assertEqual("%.2f" % d['cost_saving_10th'], '-32.73')

        # Practice with no prescribing of either.
        url = '/api/1.0/measure_by_practice/'
        url += '?org=B82010&measure=rosuvastatin&format=json'
        response = self.client.get(url, follow=True)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(len(data['measures'][0]['data']), 1)
        d = data['measures'][0]['data'][0]
        self.assertEqual(d['numerator'], 0)
        self.assertEqual(d['denominator'], 0)
        self.assertEqual(d['percentile'], None)
        self.assertEqual(d['calc_value'], None)
        self.assertEqual(d['cost_saving_10th'], 0.0)

    def test_api_all_measures_by_practice(self):
        url = '/api/1.0/measure_by_practice/'
        url += '?org=C84001&format=json'
        response = self.client.get(url, follow=True)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(len(data['measures'][0]['data']), 1)
        d = data['measures'][0]['data'][0]
        self.assertEqual(d['numerator'], 1000)
        self.assertEqual(d['denominator'], 11000)
        self.assertEqual(d['percentile'], 25)
        self.assertEqual("%.4f" % d['calc_value'], '0.0909')
