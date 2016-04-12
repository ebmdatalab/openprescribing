import os
import unittest
from django.core.management import call_command
from django.test import TestCase
from frontend.models import SHA, PCT, Practice, Measure, MeasureValue, \
    MeasureGlobal, Prescription, Chemical
from common import utils


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
        call_command('import_hscic_prescribing', *args, **new_opts)


def tearDownModule():
    call_command('flush', verbosity=0, interactive=False)


class CommandsTestCase(TestCase):

    def test_import_measure(self):
        month = '2015-09-01'
        measure_id = 'rosuvastatin'
        args = []
        opts = {
            'month': month,
            'measure': measure_id
        }
        call_command('import_measures', *args, **opts)

        m = Measure.objects.get(id=measure_id)
        self.assertEqual(m.name, 'Rosuvastatin vs. Atorvastatin')

        p = Practice.objects.get(code='C84001')
        mv = MeasureValue.objects.get(measure=m, month=month, practice=p)
        self.assertEqual(mv.numerator, 1000)
        self.assertEqual(mv.denominator, 11000)
        self.assertEqual("%.4f" % mv.calc_value, '0.0909')
        self.assertEqual(mv.num_items, 10)
        self.assertEqual(mv.denom_items, 110)
        self.assertEqual(mv.num_cost, 1000.00)
        self.assertEqual(mv.denom_cost, 2000.00)
        self.assertEqual(mv.num_quantity, 1000)
        self.assertEqual(mv.denom_quantity, 11000)
        self.assertEqual(mv.percentile, 25)
        self.assertEqual("%.2f" % mv.cost_saving_10th, '540.00')
        self.assertEqual("%.2f" % mv.cost_saving_25th, '0.00')
        self.assertEqual("%.2f" % mv.cost_saving_50th, '-2400.00')
        self.assertEqual("%.2f" % mv.cost_saving_75th, '-6030.00')
        self.assertEqual("%.2f" % mv.cost_saving_90th, '-7812.00')

        p = Practice.objects.get(code='B82010')
        mv = MeasureValue.objects.get(measure=m, month=month, practice=p)
        self.assertEqual(mv.numerator, 0)
        self.assertEqual(mv.denominator, 0)
        self.assertEqual(mv.percentile, None)
        self.assertEqual(mv.calc_value, None)
        self.assertEqual(mv.cost_saving_10th, 0)
        self.assertEqual(mv.cost_saving_90th, 0)

        p = Practice.objects.get(code='A85017')
        mv = MeasureValue.objects.get(measure=m, month=month, practice=p)
        self.assertEqual(mv.numerator, 1000)
        self.assertEqual(mv.denominator, 1000)
        self.assertEqual(mv.calc_value, 1)
        self.assertEqual(mv.percentile, 100)
        self.assertEqual("%.2f" % mv.cost_saving_10th, '867.27')
        self.assertEqual("%.2f" % mv.cost_saving_90th, '108.00')

        p = Practice.objects.get(code='A86030')
        mv = MeasureValue.objects.get(measure=m, month=month, practice=p)
        self.assertEqual(mv.numerator, 0)
        self.assertEqual(mv.denominator, 1000)
        self.assertEqual(mv.calc_value, 0)
        self.assertEqual(mv.percentile, 0)
        self.assertEqual("%.2f" % mv.cost_saving_10th, '-32.73')
        self.assertEqual("%.2f" % mv.cost_saving_90th, '-792.00')

        mg = MeasureGlobal.objects.get(measure=m, month=month)
        self.assertEqual(mg.numerator, 82000)
        self.assertEqual(mg.denominator, 143000)
        self.assertEqual(mg.num_items, 820)
        self.assertEqual(mg.denom_items, 1430)
        self.assertEqual(mg.num_cost, 82000)
        self.assertEqual(mg.denom_cost, 88100)
        self.assertEqual(mg.num_quantity, 82000)
        self.assertEqual(mg.denom_quantity, 143000)
        self.assertEqual("%.4f" % mg.calc_value, '0.5734')
        self.assertEqual("%.4f" % mg.practice_10th, '0.0364')
        self.assertEqual("%.4f" % mg.practice_25th, '0.0909')
        self.assertEqual("%.4f" % mg.practice_50th, '0.3333')
        self.assertEqual("%.4f" % mg.practice_75th, '0.7000')
        self.assertEqual("%.4f" % mg.practice_90th, '0.8800')
        self.assertEqual("%.2f" % mg.cost_saving_10th, '69152.73')
        self.assertEqual("%.2f" % mg.cost_saving_25th, '62181.82')
        self.assertEqual("%.2f" % mg.cost_saving_50th, '33600.00')
        self.assertEqual("%.2f" % mg.cost_saving_75th, '270.00')
        self.assertEqual("%.2f" % mg.cost_saving_90th, '108.00')
