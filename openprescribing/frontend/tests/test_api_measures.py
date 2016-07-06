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
    bassetlaw = PCT.objects.create(code='02Q', org_type='CCG')
    lincs_west = PCT.objects.create(code='04D', org_type='CCG')
    lincs_east = PCT.objects.create(code='03T', org_type='CCG')
    Chemical.objects.create(bnf_code='0703021Q0',
                            chem_name='Desogestrel')
    Practice.objects.create(code='C84001', ccg=bassetlaw,
                            name='LARWOOD SURGERY', setting=4)
    Practice.objects.create(code='C84024', ccg=bassetlaw,
                            name='NEWGATE MEDICAL GROUP', setting=4)
    Practice.objects.create(code='B82005', ccg=bassetlaw,
                            name='PRIORY MEDICAL GROUP', setting=4,
                            open_date='2015-01-01')
    Practice.objects.create(code='B82010', ccg=bassetlaw,
                            name='RIPON SPA SURGERY', setting=4)
    Practice.objects.create(code='A85017', ccg=bassetlaw,
                            name='BEWICK ROAD SURGERY', setting=4)
    Practice.objects.create(code='A86030', ccg=bassetlaw,
                            name='BETTS AVENUE MEDICAL GROUP', setting=4)
    # Ensure we only include open practices in our calculations.
    Practice.objects.create(code='B82008', ccg=bassetlaw,
                            name='NORTH HOUSE SURGERY', setting=4,
                            open_date='2010-04-01',
                            close_date='2012-01-01')
    # Ensure we only include standard practices in our calculations.
    Practice.objects.create(code='Y00581', ccg=bassetlaw,
                            name='BASSETLAW DRUG & ALCOHOL SERVICE',
                            setting=1)
    Practice.objects.create(code='C83051', ccg=lincs_west,
                            name='ABBEY MEDICAL PRACTICE', setting=4)
    Practice.objects.create(code='C83019', ccg=lincs_east,
                            name='BEACON MEDICAL PRACTICE', setting=4)

    args = []
    db_name = 'test_' + utils.get_env_setting('DB_NAME')
    db_user = utils.get_env_setting('DB_USER')
    db_pass = utils.get_env_setting('DB_PASS')
    test_file = 'frontend/tests/fixtures/commands/'
    test_file += 'T201509PDPI+BNFT_formatted.csv'
    new_opts = {
        'db_name': db_name,
        'db_user': db_user,
        'db_pass': db_pass,
        'filename': test_file
    }
    management.call_command('import_hscic_prescribing', *args, **new_opts)

    month = '2015-09-01'
    measure_id = 'cerazette'
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
        url = '/api/1.0/measure/?measure=cerazette&format=json'
        response = self.client.get(url, follow=True)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['measures'][0]['name'],
                         'Cerazette vs. Desogestrel')
        self.assertEqual(data['measures'][0]['description'][:10], 'Total quan')
        self.assertEqual(data['measures'][0][
                         'why_it_matters'][:10], 'This is th')
        self.assertEqual(data['measures'][0]['is_cost_based'], True)
        self.assertEqual(data['measures'][0]['is_percentage'], True)
        self.assertEqual(data['measures'][0]['low_is_good'], True)
        self.assertEqual(len(data['measures'][0]['data']), 1)
        d = data['measures'][0]['data'][0]
        self.assertEqual(d['numerator'], 85500)
        self.assertEqual(d['denominator'], 181500)
        self.assertEqual("%.4f" % d['calc_value'], '0.4711')
        self.assertEqual("%.4f" % d['percentiles']['practice']['10'], '0.0419')
        self.assertEqual("%.4f" % d['percentiles']['practice']['50'], '0.1176')
        self.assertEqual("%.4f" % d['percentiles']['practice']['90'], '0.8200')
        self.assertEqual("%.4f" % d['percentiles']['ccg']['10'], '0.0793')
        self.assertEqual("%.4f" % d['percentiles']['ccg']['50'], '0.1176')
        self.assertEqual("%.4f" % d['percentiles']['ccg']['90'], '0.4823')
        self.assertEqual("%.2f" % d['cost_savings'][
                         'practice']['10'], '70149.77')
        self.assertEqual("%.2f" % d['cost_savings'][
                         'practice']['50'], '59029.41')
        self.assertEqual("%.2f" % d['cost_savings'][
                         'practice']['90'], '162.00')
        self.assertEqual("%.2f" % d['cost_savings']['ccg']['10'], '64174.56')
        self.assertEqual("%.2f" % d['cost_savings']['ccg']['50'], '58658.82')
        self.assertEqual("%.2f" % d['cost_savings']['ccg']['90'], '11731.76')

    def test_api_all_measures_global(self):
        url = '/api/1.0/measure/?format=json'
        response = self.client.get(url, follow=True)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(len(data['measures'][0]['data']), 1)
        self.assertEqual(data['measures'][0]['low_is_good'], True)
        d = data['measures'][0]['data'][0]
        self.assertEqual(d['numerator'], 85500)
        self.assertEqual(d['denominator'], 181500)
        self.assertEqual("%.4f" % d['calc_value'], '0.4711')

    def test_api_measure_by_all_ccgs(self):
        url = '/api/1.0/measure_by_ccg/'
        url += '?measure=cerazette&format=json'
        response = self.client.get(url, follow=True)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(len(data['measures'][0]['data']), 3)
        self.assertEqual(data['measures'][0]['low_is_good'], True)
        d = data['measures'][0]['data'][0]
        self.assertEqual(d['pct_id'], '03T')
        self.assertEqual(d['numerator'], 2000)
        self.assertEqual(d['denominator'], 17000)
        self.assertEqual(d['percentile'], 50)
        self.assertEqual("%.4f" % d['calc_value'], '0.1176')

    def test_api_measure_by_ccg(self):
        url = '/api/1.0/measure_by_ccg/'
        url += '?org=02Q&measure=cerazette&format=json'
        response = self.client.get(url, follow=True)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(len(data['measures'][0]['data']), 1)
        self.assertEqual(data['measures'][0]['low_is_good'], True)
        d = data['measures'][0]['data'][0]
        self.assertEqual(d['numerator'], 82000)
        self.assertEqual(d['denominator'], 143000)
        self.assertEqual(d['percentile'], 100)
        self.assertEqual("%.4f" % d['calc_value'], '0.5734')
        self.assertEqual("%.2f" % d['cost_savings']['10'], '63588.51')
        self.assertEqual("%.2f" % d['cost_savings']['50'], '58658.82')
        self.assertEqual("%.2f" % d['cost_savings']['90'], '11731.76')

    def test_api_all_measures_by_ccg(self):
        url = '/api/1.0/measure_by_ccg/'
        url += '?org=02Q&format=json'
        response = self.client.get(url, follow=True)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(len(data['measures'][0]['data']), 1)
        self.assertEqual(data['measures'][0]['low_is_good'], True)
        d = data['measures'][0]['data'][0]
        self.assertEqual(d['numerator'], 82000)
        self.assertEqual(d['denominator'], 143000)
        self.assertEqual(d['percentile'], 100)
        self.assertEqual("%.4f" % d['calc_value'], '0.5734')

    def test_api_measure_by_practice(self):
        url = '/api/1.0/measure_by_practice/'
        url += '?org=C84001&measure=cerazette&format=json'
        response = self.client.get(url, follow=True)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(len(data['measures'][0]['data']), 1)
        self.assertEqual(data['measures'][0]['low_is_good'], True)
        d = data['measures'][0]['data'][0]
        self.assertEqual(d['numerator'], 1000)
        self.assertEqual(d['denominator'], 11000)
        self.assertEqual("%.2f" % d['percentile'], '33.33')
        self.assertEqual("%.4f" % d['calc_value'], '0.0909')
        self.assertEqual("%.2f" % d['cost_savings']['10'], '485.58')
        self.assertEqual("%.2f" % d['cost_savings']['50'], '-264.71')
        self.assertEqual("%.2f" % d['cost_savings']['90'], '-7218.00')

        # Practice with only Cerazette prescribing.
        url = '/api/1.0/measure_by_practice/'
        url += '?org=A85017&measure=cerazette&format=json'
        response = self.client.get(url, follow=True)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        d = data['measures'][0]['data'][0]
        self.assertEqual(d['numerator'], 1000)
        self.assertEqual(d['denominator'], 1000)
        self.assertEqual(d['percentile'], 100)
        self.assertEqual(d['calc_value'], 1)
        self.assertEqual("%.2f" % d['cost_savings']['10'], '862.33')

        # Practice with only Deso prescribing.
        url = '/api/1.0/measure_by_practice/'
        url += '?org=A86030&measure=cerazette&format=json'
        response = self.client.get(url, follow=True)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(len(data['measures'][0]['data']), 1)
        d = data['measures'][0]['data'][0]
        self.assertEqual(d['numerator'], 0)
        self.assertEqual(d['denominator'], 1000)
        self.assertEqual(d['percentile'], 0)
        self.assertEqual(d['calc_value'], 0)
        self.assertEqual("%.2f" % d['cost_savings']['10'], '-37.67')

        # Practice with no prescribing of either.
        url = '/api/1.0/measure_by_practice/'
        url += '?org=B82010&measure=cerazette&format=json'
        response = self.client.get(url, follow=True)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(len(data['measures'][0]['data']), 1)
        d = data['measures'][0]['data'][0]
        self.assertEqual(d['numerator'], 0)
        self.assertEqual(d['denominator'], 0)
        self.assertEqual(d['percentile'], None)
        self.assertEqual(d['calc_value'], None)
        self.assertEqual(d['cost_savings']['10'], 0.0)

    def test_api_all_measures_by_practice(self):
        url = '/api/1.0/measure_by_practice/'
        url += '?org=C84001&format=json'
        response = self.client.get(url, follow=True)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(len(data['measures'][0]['data']), 1)
        self.assertEqual(data['measures'][0]['low_is_good'], True)
        d = data['measures'][0]['data'][0]
        self.assertEqual(d['numerator'], 1000)
        self.assertEqual(d['denominator'], 11000)
        self.assertEqual("%.2f" % d['percentile'], '33.33')
        self.assertEqual("%.4f" % d['calc_value'], '0.0909')
