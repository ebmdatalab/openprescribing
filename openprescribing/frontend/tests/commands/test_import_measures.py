import os
import argparse
from numbers import Number
from django.core.management import call_command
from django.test import TestCase
from test.test_support import EnvironmentVarGuard

from frontend.models import SHA, PCT, Practice, Measure
from frontend.models import MeasureValue, MeasureGlobal, Chemical
from frontend.management.commands.import_measures import Command
from frontend.management.commands.import_measures \
    import PRESCRIBING_TABLE_NAME, PRACTICES_TABLE_NAME

from ebmdatalab import bigquery


def isclose(a, b, rel_tol=0.001, abs_tol=0.0):
    if isinstance(a, Number) and isinstance(b, Number):
        return abs(a-b) <= max(rel_tol * max(abs(a), abs(b)), abs_tol)
    else:
        return a == b


class ArgumentTestCase(TestCase):
    def test_months_parsed_from_hscic_filename(self):
        opts = [
            '--month_from_prescribing_filename',
            'data/prescribing/2016_03/T201603PDPI BNFT_formatted.CSV'
        ]
        parser = argparse.ArgumentParser()
        cmd = Command()
        parser = cmd.create_parser("import_measures", "")
        options = parser.parse_args(opts)
        result = cmd.parse_options(options.__dict__)
        self.assertEqual(result['start_date'], '2016-03-01')
        self.assertEqual(result['end_date'], '2016-03-01')


class BehaviourTestCase(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.env = EnvironmentVarGuard()
        cls.env.set('DB_NAME', 'test_' + os.environ['DB_NAME'])
        with cls.env:
            cls._createData()

    @classmethod
    def tearDownClass(cls):
        with cls.env:
            call_command('flush', verbosity=0, interactive=False)

    def test_measure_is_created(self):
        m = Measure.objects.get(id='cerazette')
        self.assertEqual(m.name, 'Cerazette vs. Desogestrel')
        self.assertEqual(m.description[:10], 'Total quan')
        self.assertEqual(m.why_it_matters[:10], 'This is th')
        self.assertEqual(m.low_is_good, True)

    def test_practice_general(self):
        month = '2015-09-01'
        measure = Measure.objects.get(id='cerazette')
        expected = {
            'C84001': {
                'numerator': 1000,
                'denominator': 11000,
                'calc_value': 0.0909,
                'num_items': 10,
                'denom_items': 110,
                'num_cost': 1000.0,
                'denom_cost': 2000,
                'denom_quantity': 11000,
                'percentile': 33.33,
                'pct.code': '02Q',
                'cost_savings': {
                    '10': 485.58,
                    '20': 167.44,
                    '50': -264.71,
                    '70': -3126.00,
                    '90': -7218.00
                }
            }
        }
        self._assertExpectedMeasureValue(measure, month, expected)

    def test_practice_with_no_prescribing(self):
        month = '2015-09-01'
        measure = Measure.objects.get(id='cerazette')
        expected = {
            'B82010': {
                'numerator': 0,
                'denominator': 0,
                'calc_value': None,
                'num_items': None,
                'denom_items': None,
                'num_cost': None,
                'denom_cost': None,
                'denom_quantity': None,
                'percentile': None,
                'cost_savings': {
                    '10': 0,
                    '90': 0
                }
            }
        }
        self._assertExpectedMeasureValue(measure, month, expected)

    def test_practice_with_positive_cost_savings(self):
        month = '2015-09-01'
        measure = Measure.objects.get(id='cerazette')
        expected = {
            'A85017': {
                'numerator': 1000,
                'denominator': 1000,
                'calc_value': 1,
                'percentile': 100,
                'cost_savings': {
                    '10': 862.33,
                    '90': 162.00
                }
            }
        }
        self._assertExpectedMeasureValue(measure, month, expected)

    def test_practice_with_negative_cost_savings(self):
        month = '2015-09-01'
        measure = Measure.objects.get(id='cerazette')
        expected = {
            'A86030': {
                'numerator': 0,
                'denominator': 1000,
                'calc_value': 0,
                'percentile': 0,
                'cost_savings': {
                    '10': -37.67,
                    '90': -738.00
                }
            }
        }
        self._assertExpectedMeasureValue(measure, month, expected)

    def test_practice_in_top_quartile(self):
        month = '2015-09-01'
        measure = Measure.objects.get(id='cerazette')
        expected = {
            'C83051': {
                'numerator': 1500,
                'denominator': 21500,
                'calc_value': 0.0698,
                'percentile': 16.67,
                'cost_savings': {
                    '10': 540.00,
                    '90': -14517.00
                }
            }
        }
        self._assertExpectedMeasureValue(measure, month, expected)

    def test_practice_at_median(self):
        month = '2015-09-01'
        measure = Measure.objects.get(id='cerazette')
        expected = {
            'C83019': {
                'numerator': 2000,
                'denominator': 17000,
                'calc_value': 0.1176,
                'percentile': 50,
                'cost_savings': {
                    '10': 1159.53,
                    '90': -10746.00
                }
            }
        }
        self._assertExpectedMeasureValue(measure, month, expected)

    def test_import_measurevalue_by_practice_with_different_payments(self):
        m = Measure.objects.get(id='cerazette')
        month = '2015-10-01'

        p = Practice.objects.get(code='C83051')
        mv = MeasureValue.objects.get(measure=m, month=month, practice=p)
        self.assertEqual("%.2f" % mv.cost_savings['50'], '0.00')

        p = Practice.objects.get(code='C83019')
        mv = MeasureValue.objects.get(measure=m, month=month, practice=p)
        self.assertEqual("%.2f" % mv.cost_savings['50'], '325.58')

        p = Practice.objects.get(code='A86030')
        mv = MeasureValue.objects.get(measure=m, month=month, practice=p)
        self.assertEqual("%.2f" % mv.cost_savings['50'], '-42.86')

    def test_import_measurevalue_by_ccg(self):
        m = Measure.objects.get(id='cerazette')
        month = '2015-09-01'

        ccg = PCT.objects.get(code='02Q')
        mv = MeasureValue.objects.get(
            measure=m, month=month, pct=ccg, practice=None)
        self.assertEqual(mv.numerator, 82000)
        self.assertEqual(mv.denominator, 143000)
        self.assertEqual("%.4f" % mv.calc_value, '0.5734')
        self.assertEqual(mv.percentile, 100)
        self.assertEqual("%.2f" % mv.cost_savings['10'], '63588.51')
        self.assertEqual("%.2f" % mv.cost_savings['30'], '61123.67')
        self.assertEqual("%.2f" % mv.cost_savings['50'], '58658.82')
        self.assertEqual("%.2f" % mv.cost_savings['80'], '23463.53')
        self.assertEqual("%.2f" % mv.cost_savings['90'], '11731.76')

        ccg = PCT.objects.get(code='04D')
        mv = MeasureValue.objects.get(
            measure=m, month=month, pct=ccg, practice=None)
        self.assertEqual(mv.numerator, 1500)
        self.assertEqual(mv.denominator, 21500)
        self.assertEqual("%.4f" % mv.calc_value, '0.0698')
        self.assertEqual(mv.percentile, 0)

        ccg = PCT.objects.get(code='03T')
        mv = MeasureValue.objects.get(
            measure=m, month=month, pct=ccg, practice=None)
        self.assertEqual(mv.numerator, 2000)
        self.assertEqual(mv.denominator, 17000)
        self.assertEqual("%.4f" % mv.calc_value, '0.1176')
        self.assertEqual(mv.percentile, 50)

    def test_import_measureglobal(self):
        month = '2015-09-01'
        measure = Measure.objects.get(id='cerazette')
        expected = {
            '_global_': {
                'numerator': 85500,
                'denominator': 181500,
                'num_items': 855,
                'denom_items': 1815,
                'num_cost': 85500,
                'denom_cost': 95100,
                'num_quantity': 85500,
                'denom_quantity': 181500,
                'calc_value': 0.4711,
                'percentiles': {
                    'practice': {
                        '10': 0.0419,
                        '20': 0.0740,
                        '50': 0.1176,
                        '70': 0.4067,
                        '90': 0.8200
                    },
                    'ccg': {
                        '10': 0.0793,
                        '30': 0.0985,
                        '50': 0.1176,
                        '80': 0.3911,
                        '90': 0.4823
                    },
                },
                'cost_savings': {
                    'practice': {
                        '10': 70149.77,
                        '20': 65011.21,
                        '50': 59029.41,
                        '70': 26934.00,
                        '90': 162.00
                    },
                    'ccg': {
                        '10': 64174.56,
                        '30': 61416.69,
                        '50': 58658.82,
                        '80': 23463.53,
                        '90': 11731.76
                    },
                },
            }
        }
        self._assertExpectedMeasureValue(measure, month, expected)

    @classmethod
    def _createData(cls):
        SHA.objects.create(code='Q51')
        bassetlaw = PCT.objects.create(code='02Q', org_type='CCG')
        lincs_west = PCT.objects.create(code='04D', org_type='CCG')
        lincs_east = PCT.objects.create(code='03T', org_type='CCG',
                                        open_date='2013-04-01',
                                        close_date='2015-01-01')
        Chemical.objects.create(bnf_code='0703021Q0',
                                chem_name='Desogestrel')
        Chemical.objects.create(bnf_code='0408010A0',
                                chem_name='Levetiracetam')
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
                                name='NORTH SURGERY', setting=4,
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
        test_file = 'frontend/tests/fixtures/commands/'
        test_file += 'T201509PDPI+BNFT_formatted.csv'
        if 'SKIP_BQ_LOAD' not in os.environ:
            bigquery.load_prescribing_data_from_file(
                'measures', 'test_' + PRESCRIBING_TABLE_NAME, test_file)
            bigquery.load_data_from_pg(
                'hscic', 'test_' + PRACTICES_TABLE_NAME, 'frontend_practice',
                bigquery.PRACTICE_SCHEMA)
        month = '2015-09-01'
        measure_id = 'cerazette'
        args = []
        opts = {
            'month': month,
            'measure': measure_id,
            'test_mode': True,
        }
        call_command('import_measures', *args, **opts)

        month = '2015-10-01'
        measure_id = 'cerazette'
        args = []
        opts = {
            'month': month,
            'measure': measure_id,
            'test_mode': True,
        }
        call_command('import_measures', *args, **opts)

    def _walk(self, mv, data):
        for k, v in data.items():
            if '.' in k:
                relation, attr = k.split('.')
                model = getattr(mv, relation)
                actual = getattr(model, attr)
                expected = v
                identifier = k
            elif isinstance(v, dict):
                field = getattr(mv, k)
                for k2, v2 in v.items():
                    actual = field.get(k2)
                    expected = v2
                    identifier = "%s[%s]" % (k, k2)
                    if isinstance(v2, dict):
                        for k3, v3 in v2.items():
                            yield actual.get(k3), v3, "[%s]" % k3
                    else:
                        yield actual, expected, identifier

            else:
                actual = getattr(mv, k)
                expected = v
                identifier = k
                yield actual, expected, identifier

    def _assertExpectedMeasureValue(self, measure, month, expected):
        for practice_id, data in expected.items():
            if practice_id == '_global_':
                mv = MeasureGlobal.objects.get(
                    measure=measure, month=month)
            else:
                p = Practice.objects.get(code=practice_id)
                mv = MeasureValue.objects.get(
                    measure=measure, month=month, practice=p)
                for actual, expected, identifier in self._walk(mv, data):
                    if isinstance(expected, Number):
                        self.assert_(
                            isclose(actual, expected),
                            "got %s for %s, expected ~ %s" % (
                                actual, identifier, expected))
                    else:
                        self.assert_(
                            actual == expected,
                            "got %s for %s, expected %s" % (
                                actual, identifier, expected))
