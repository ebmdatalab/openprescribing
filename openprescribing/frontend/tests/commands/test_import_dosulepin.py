import os
import unittest
from django.core.management import call_command
from django.test import TestCase
from frontend.models import SHA, PCT, Practice, Measure, MeasureValue, \
    MeasureGlobal, Prescription, Chemical
from common import utils


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


def tearDownModule():
    call_command('flush', verbosity=0, interactive=False)


class CommandsTestCase(TestCase):

    def test_import_dosulepin(self):
        month = '2013-09-01'
        args = []
        opts = {
            'month': month
        }
        call_command('import_dosulepin', *args, **opts)

        m = Measure.objects.get(id='ktt8_dosulepin')
        self.assertEqual(m.name, 'KTT8: Dosulepin: % items')

        p1 = Practice.objects.get(code='C84001')
        mv = MeasureValue.objects.get(measure=m, month=month, practice=p1)
        self.assertEqual(mv.numerator, 34)
        self.assertEqual(mv.denominator, 415)
        self.assertEqual("%.4f" % mv.calc_value, '0.0819')
        self.assertEqual(mv.percentile, 0.0)

        p2 = Practice.objects.get(code='C84024')
        mv = MeasureValue.objects.get(measure=m, month=month, practice=p2)
        self.assertEqual(mv.numerator, 34)
        self.assertEqual(mv.denominator, 2+34)
        self.assertEqual("%.4f" % mv.calc_value, '0.9444')
        self.assertEqual(mv.percentile, 99.0)

        p3 = Practice.objects.get(code='Y00581')
        mv = MeasureValue.objects.get(measure=m, month=month, practice=p3)
        self.assertEqual(mv.numerator, None)
        self.assertEqual(mv.denominator, None)
        self.assertEqual(mv.calc_value, None)
        self.assertEqual(mv.percentile, None)

        mg = MeasureGlobal.objects.get(measure=m, month=month)
        self.assertEqual("%.4f" % mg.practice_10th, '0.1682')
        self.assertEqual("%.4f" % mg.practice_90th, '0.8582')
