from numbers import Number
import argparse
import json
import os

from gcutils.bigquery import Client
from mock import patch
from mock import MagicMock

from django.conf import settings
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase

from frontend.bq_schemas import CCG_SCHEMA, PRACTICE_SCHEMA, PRESCRIBING_SCHEMA
from frontend.management.commands.import_measures import Command
from frontend.management.commands.import_measures import parse_measures
from frontend.management.commands.import_measures import check_definition
from frontend.models import ImportLog
from frontend.models import Measure
from frontend.models import MeasureValue, MeasureGlobal, Chemical
from frontend.models import PCT
from frontend.models import Practice
from frontend.models import STP
from frontend.models import RegionalTeam

from google.api_core.exceptions import BadRequest

def isclose(a, b, rel_tol=0.001, abs_tol=0.0):
    if isinstance(a, Number) and isinstance(b, Number):
        return abs(a-b) <= max(rel_tol * max(abs(a), abs(b)), abs_tol)
    else:
        return a == b


def working_measure_files():
    fpath = settings.REPO_ROOT
    fname = os.path.join(
        fpath, ('openprescribing/frontend/tests/fixtures/measure_definitions/'
                'cerazette.json'))
    return [fname]


def broken_json_measure_files():
    fpath = settings.REPO_ROOT
    fname = os.path.join(
        fpath, ('openprescribing/frontend/tests/fixtures/measure_definitions/'
                'bad_json.json'))
    return [fname]


def broken_sql_measure_files():
    fpath = settings.REPO_ROOT
    fname = os.path.join(
        fpath, ('openprescribing/frontend/tests/fixtures/measure_definitions/'
                'bad_sql.json'))
    return [fname]


def parse_args(*opts_args):
    """Duplicate what Django does to parse arguments.

    See `django.core.management.__init__.call_command` for details

    """
    parser = argparse.ArgumentParser()
    cmd = Command()
    parser = cmd.create_parser("import_measures", "")
    options = parser.parse_args(opts_args)
    return cmd.parse_options(options.__dict__)


@patch('frontend.management.commands.import_measures.get_measure_definition_files',
       new=MagicMock(return_value=working_measure_files()))
class ArgumentTestCase(TestCase):
    def test_start_and_end_dates(self):
        with self.assertRaises(CommandError):
            parse_args(
                '--start_date',
                '1999-01-01'
            )
        with self.assertRaises(CommandError):
            parse_args(
                '--end_date',
                '1999-01-01'
            )
        result = parse_args(
            '--start_date',
            '1998-01-01',
            '--end_date',
            '1999-01-01'
        )
        self.assertEqual(result['start_date'], '1998-01-01')
        self.assertEqual(result['end_date'], '1999-01-01')


@patch('frontend.management.commands.import_measures.get_measure_definition_files',
       new=MagicMock(return_value=working_measure_files()))
class UnitTests(TestCase):
    """Unit tests with mocked bigquery. Many of the functional
    tests could be moved hree.

    """
    fixtures = ['measures']

    @patch('common.utils.db')
    def test_reconstructor_not_called_when_measures_specified(self, db):
        from frontend.management.commands.import_measures \
            import conditional_constraint_and_index_reconstructor
        with conditional_constraint_and_index_reconstructor(
                {'measure': 'thingy'}):
            pass
        execute = db.connection.cursor.return_value.__enter__.return_value.execute
        execute.assert_not_called()

    @patch('common.utils.db')
    def test_reconstructor_called_when_no_measures_specified(self, db):
        from frontend.management.commands.import_measures \
            import conditional_constraint_and_index_reconstructor
        with conditional_constraint_and_index_reconstructor({'measure': None}):
            pass
        execute = db.connection.cursor.return_value.__enter__.return_value.execute
        execute.assert_called()


class BigqueryFunctionalTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        regional_team_54 = RegionalTeam.objects.create(code='Y54')
        regional_team_55 = RegionalTeam.objects.create(code='Y55')
        stp_1 = STP.objects.create(ons_code='E00000001')
        stp_2 = STP.objects.create(ons_code='E00000002')

        bassetlaw = PCT.objects.create(code='02Q', org_type='CCG', stp=stp_1,
                                       regional_team=regional_team_54)
        lincs_west = PCT.objects.create(code='04D', org_type='CCG', stp=stp_2,
                                        regional_team=regional_team_55)
        lincs_east = PCT.objects.create(code='03T', org_type='CCG',
                                        open_date='2013-04-01',
                                        close_date='2015-01-01',
                                        stp=stp_2,
                                        regional_team=regional_team_55)
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
        Practice.objects.create(code='C83051', ccg=lincs_west,
                                name='ABBEY MEDICAL PRACTICE', setting=4)
        Practice.objects.create(code='C83019', ccg=lincs_east,
                                name='BEACON MEDICAL PRACTICE', setting=4)
        # Ensure we only include open practices in our calculations.
        Practice.objects.create(code='B82008', ccg=bassetlaw,
                                name='NORTH SURGERY', setting=4,
                                open_date='2010-04-01',
                                close_date='2012-01-01')
        # Ensure we only include standard practices in our calculations.
        Practice.objects.create(code='Y00581', ccg=bassetlaw,
                                name='BASSETLAW DRUG & ALCOHOL SERVICE',
                                setting=1)

        measure = Measure.objects.create(
            id='cerazette',
            name='Cerazette vs. Desogestrel',
            title='Prescribing of...',
            tags=['core'],
            numerator_bnf_codes=[],
        )

        # We expect this MeasureValue to be deleted because it is older than
        # five years.
        MeasureValue.objects.create(
            measure=measure,
            pct_id='02Q',
            month='2000-01-01',
        )

        # We expect this MeasureValue to be unchanged
        MeasureValue.objects.create(
            measure=measure,
            pct_id='02Q',
            month='2015-08-01',
        )

        # We expect this MeasureValue to be updated
        MeasureValue.objects.create(
            measure=measure,
            pct_id='02Q',
            month='2015-09-01',
        )

        ImportLog.objects.create(
            category='prescribing',
            current_at='2018-04-01',
            filename='/tmp/prescribing.csv',
        )
        if 'SKIP_BQ_LOAD' in os.environ:
            assert 'BQ_NONCE' in os.environ, "Specify BQ_NONCE to reuse fixtures"

        if 'SKIP_BQ_LOAD' not in os.environ:
            fixtures_path = os.path.join(
                'frontend', 'tests', 'fixtures', 'commands')

            prescribing_fixture_path = os.path.join(
                fixtures_path,
                'prescribing_bigquery_fixture.csv'
            )
            # TODO Make this a table with a view (see
            # generate_presentation_replacements), and put it in the correct
            # dataset ('hscic', not 'measures').
            client = Client('measures')
            table = client.get_or_create_table(
                'normalised_prescribing_legacy',
                PRESCRIBING_SCHEMA
            )
            table.insert_rows_from_csv(prescribing_fixture_path)

            practices_fixture_path = os.path.join(
                fixtures_path,
                'practices.csv'
            )
            client = Client('hscic')
            table = client.get_or_create_table('practices', PRACTICE_SCHEMA)
            table.insert_rows_from_csv(practices_fixture_path)

            ccgs_fixture_path = os.path.join(
                fixtures_path,
                'ccgs.csv'
            )
            table = client.get_or_create_table('ccgs', CCG_SCHEMA)
            table.insert_rows_from_csv(ccgs_fixture_path)

        opts = {
            'month': '2015-09-01',
            'measure': 'cerazette',
            'v': 3
        }
        with patch('frontend.management.commands.import_measures'
                   '.get_measure_definition_files',
                   new=MagicMock(return_value=working_measure_files())):
            call_command('import_measures', **opts)

    @patch('frontend.management.commands.import_measures'
           '.get_measure_definition_files',
           new=MagicMock(return_value=broken_json_measure_files()))
    def test_check_definition_bad_json(self):
        with self.assertRaises(ValueError) as command_error:
            call_command('import_measures', check=True)
        self.assertIn("Problems parsing JSON", str(command_error.exception))

    @patch('frontend.management.commands.import_measures'
           '.get_measure_definition_files',
           new=MagicMock(return_value=broken_sql_measure_files()))
    def test_check_definition_bad_sql(self):
        with self.assertRaises(BadRequest) as command_error:
            call_command('import_measures', check=True)
        self.assertIn("SQL error", str(command_error.exception))

    def test_import_measurevalue_by_practice_with_different_payments(self):
        month = '2015-10-01'
        measure_id = 'cerazette'
        args = []
        opts = {
            'month': month,
            'measure': measure_id,
            'v': 3
        }
        with patch('frontend.management.commands.import_measures'
                   '.get_measure_definition_files',
                   new=MagicMock(return_value=working_measure_files())):
            call_command('import_measures', *args, **opts)

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

    def test_measure_is_updated(self):
        m = Measure.objects.get(id='cerazette')
        self.assertEqual(m.name, 'Cerazette vs. Desogestrel')
        self.assertEqual(m.description[:10], 'Total quan')
        self.assertEqual(m.why_it_matters[:10], 'This is th')
        self.assertEqual(m.low_is_good, True)

    def test_old_measure_value_deleted(self):
        self.assertEqual(
            MeasureValue.objects.filter(
                measure='cerazette',
                pct='02Q',
                month='2000-01-01',
            ).count(),
            0
        )

    def test_not_so_old_measure_value_not_deleted(self):
        self.assertEqual(
            MeasureValue.objects.filter(
                measure='cerazette',
                pct='02Q',
                month='2015-08-01',
            ).count(),
            1
        )

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

    def test_ccg_at_0th_centile(self):
        month = '2015-09-01'
        measure = Measure.objects.get(id='cerazette')
        expected = {
            '04D': {
                'numerator': 1500,
                'denominator': 21500,
                'calc_value': 0.0698,
                'percentile': 0
            }
        }
        self._assertExpectedMeasureValue(measure, month, expected)

    def test_ccg_at_100th_centile(self):
        month = '2015-09-01'
        measure = Measure.objects.get(id='cerazette')
        expected = {
            '02Q': {
                'numerator': 82000,
                'denominator': 143000,
                'calc_value': 0.5734,
                'percentile': 100,
                'cost_savings': {
                    '10': 63588.51,
                    '30': 61123.67,
                    '50': 58658.82,
                    '80': 23463.53,
                    '90': 11731.76
                }
            }
        }
        self._assertExpectedMeasureValue(measure, month, expected)

    def test_ccg_at_50th_centile(self):
        month = '2015-09-01'
        measure = Measure.objects.get(id='cerazette')
        expected = {
            '03T': {
                'numerator': 2000,
                'denominator': 17000,
                'calc_value': 0.1176,
                'percentile': 50
            }
        }
        self._assertExpectedMeasureValue(measure, month, expected)

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
                        '10': 64174.56,  # this one got 62795.62
                        '30': 61416.69,
                        '50': 58658.82,
                        '80': 23463.53,
                        '90': 11731.76
                    },
                },
            }
        }
        self._assertExpectedMeasureValue(measure, month, expected)

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
                        # BQ returns strings:
                        try:
                            actual = json.loads(actual)
                        except TypeError:
                            # Already decoded it
                            pass
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
        for entity_id, data in expected.items():
            if entity_id == '_global_':
                mv = MeasureGlobal.objects.get(
                    measure=measure, month=month)
            elif len(entity_id) == 3:
                ccg = PCT.objects.get(code=entity_id)
                mv = MeasureValue.objects.get(
                    measure=measure, month=month, pct=ccg, practice=None)
            else:

                p = Practice.objects.get(code=entity_id)
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


class TestAllCurrentMeasures(TestCase):
    def test_parse_and_run_measures(self):
        measures = parse_measures()
        options = {'measure_ids': measures.keys()}
        lpzomnibus_ix = list(measures).index('lpzomnibus')
        lptrimipramine_ix = list(measures).index('lptrimipramine')

        # The order of these specific measures matters, as the SQL for
        # the omnibus measure relies on the other LP measures having
        # been calculated first
        self.assertTrue(lptrimipramine_ix < lpzomnibus_ix)

        # Now check the SQL for all the measures
        check_definition(options, '2001-01-01', '2030-01-01', True)
