from django.core.management import call_command
from django.test import TestCase
from frontend.models import SHA, PCT, Practice, Measure
from frontend.models import MeasureValue, MeasureGlobal, Chemical
from common import utils


def setUpModule():
    SHA.objects.create(code='Q51')
    bassetlaw = PCT.objects.create(code='02Q', org_type='CCG')
    lincs_west = PCT.objects.create(code='04D', org_type='CCG')
    lincs_east = PCT.objects.create(code='03T', org_type='CCG',
                                    open_date='2013-04-01',
                                    close_date='2015-01-01')
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
    call_command('import_hscic_prescribing', *args, **new_opts)

    month = '2015-09-01'
    measure_id = 'cerazette'
    args = []
    opts = {
        'month': month,
        'measure': measure_id
    }
    call_command('import_measures', *args, **opts)


def tearDownModule():
    call_command('flush', verbosity=0, interactive=False)


class CommandsTestCase(TestCase):

    def test_import_measurevalue_by_practice(self):
        m = Measure.objects.get(id='cerazette')
        self.assertEqual(m.name, 'Cerazette vs. Desogestrel')
        self.assertEqual(m.description[:10], 'Total quan')
        self.assertEqual(m.why_it_matters[:10], 'This is th')
        self.assertEqual(m.low_is_good, True)
        month = '2015-09-01'

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
        self.assertEqual("%.2f" % mv.percentile, '33.33')
        self.assertEqual(mv.pct.code, '02Q')
        self.assertEqual("%.2f" % mv.cost_savings['10'], '485.58')
        self.assertEqual("%.2f" % mv.cost_savings['20'], '167.44')
        self.assertEqual("%.2f" % mv.cost_savings['50'], '-264.71')
        self.assertEqual("%.2f" % mv.cost_savings['70'], '-3126.00')
        self.assertEqual("%.2f" % mv.cost_savings['90'], '-7218.00')

        p = Practice.objects.get(code='B82010')
        mv = MeasureValue.objects.get(measure=m, month=month, practice=p)
        self.assertEqual(mv.numerator, 0)
        self.assertEqual(mv.denominator, 0)
        self.assertEqual(mv.percentile, None)
        self.assertEqual(mv.calc_value, None)
        self.assertEqual(mv.cost_savings['10'], 0)
        self.assertEqual(mv.cost_savings['90'], 0)

        p = Practice.objects.get(code='A85017')
        mv = MeasureValue.objects.get(measure=m, month=month, practice=p)
        self.assertEqual(mv.numerator, 1000)
        self.assertEqual(mv.denominator, 1000)
        self.assertEqual(mv.calc_value, 1)
        self.assertEqual(mv.percentile, 100)
        self.assertEqual("%.2f" % mv.cost_savings['10'], '862.33')
        self.assertEqual("%.2f" % mv.cost_savings['90'], '162.00')

        p = Practice.objects.get(code='A86030')
        mv = MeasureValue.objects.get(measure=m, month=month, practice=p)
        self.assertEqual(mv.numerator, 0)
        self.assertEqual(mv.denominator, 1000)
        self.assertEqual(mv.calc_value, 0)
        self.assertEqual(mv.percentile, 0)
        self.assertEqual("%.2f" % mv.cost_savings['10'], '-37.67')
        self.assertEqual("%.2f" % mv.cost_savings['90'], '-738.00')

        p = Practice.objects.get(code='C83051')
        mv = MeasureValue.objects.get(measure=m, month=month, practice=p)
        self.assertEqual(mv.numerator, 1500)
        self.assertEqual(mv.denominator, 21500)
        self.assertEqual("%.4f" % mv.calc_value, '0.0698')
        self.assertEqual("%.2f" % mv.percentile, "16.67")
        self.assertEqual("%.2f" % mv.cost_savings['10'], '540.00')
        self.assertEqual("%.2f" % mv.cost_savings['90'], '-14517.00')

        p = Practice.objects.get(code='C83019')
        mv = MeasureValue.objects.get(measure=m, month=month, practice=p)
        self.assertEqual(mv.numerator, 2000)
        self.assertEqual(mv.denominator, 17000)
        self.assertEqual("%.4f" % mv.calc_value, '0.1176')
        self.assertEqual(mv.percentile, 50)
        self.assertEqual("%.2f" % mv.cost_savings['10'], '1159.53')
        self.assertEqual("%.2f" % mv.cost_savings['90'], '-10746.00')

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
        m = Measure.objects.get(id='cerazette')
        self.assertEqual(m.name, 'Cerazette vs. Desogestrel')
        month = '2015-09-01'

        mg = MeasureGlobal.objects.get(measure=m, month=month)
        self.assertEqual(mg.numerator, 85500)
        self.assertEqual(mg.denominator, 181500)
        self.assertEqual(mg.num_items, 855)
        self.assertEqual(mg.denom_items, 1815)
        self.assertEqual(mg.num_cost, 85500)
        self.assertEqual(mg.denom_cost, 95100)
        self.assertEqual(mg.num_quantity, 85500)
        self.assertEqual(mg.denom_quantity, 181500)
        self.assertEqual("%.4f" % mg.calc_value, '0.4711')
        self.assertEqual("%.4f" % mg.percentiles['practice']['10'], '0.0419')
        self.assertEqual("%.4f" % mg.percentiles['practice']['20'], '0.0740')
        self.assertEqual("%.4f" % mg.percentiles['practice']['50'], '0.1176')
        self.assertEqual("%.4f" % mg.percentiles['practice']['70'], '0.4067')
        self.assertEqual("%.4f" % mg.percentiles['practice']['90'], '0.8200')
        self.assertEqual("%.4f" % mg.percentiles['ccg']['10'], '0.0793')
        self.assertEqual("%.4f" % mg.percentiles['ccg']['30'], '0.0985')
        self.assertEqual("%.4f" % mg.percentiles['ccg']['50'], '0.1176')
        self.assertEqual("%.4f" % mg.percentiles['ccg']['80'], '0.3911')
        self.assertEqual("%.4f" % mg.percentiles['ccg']['90'], '0.4823')
        self.assertEqual("%.2f" % mg.cost_savings[
                         'practice']['10'], '70149.77')
        self.assertEqual("%.2f" % mg.cost_savings[
                         'practice']['20'], '65011.21')
        self.assertEqual("%.2f" % mg.cost_savings[
                         'practice']['50'], '59029.41')
        self.assertEqual("%.2f" % mg.cost_savings[
                         'practice']['70'], '26934.00')
        self.assertEqual("%.2f" % mg.cost_savings['practice']['90'], '162.00')
        self.assertEqual("%.2f" % mg.cost_savings['ccg']['10'], '64174.56')
        self.assertEqual("%.2f" % mg.cost_savings['ccg']['30'], '61416.69')
        self.assertEqual("%.2f" % mg.cost_savings['ccg']['50'], '58658.82')
        self.assertEqual("%.2f" % mg.cost_savings['ccg']['80'], '23463.53')
        self.assertEqual("%.2f" % mg.cost_savings['ccg']['90'], '11731.76')
