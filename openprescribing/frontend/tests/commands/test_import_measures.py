import argparse
import time
import csv
import tempfile
from django.core.management import call_command
from django.test import TestCase
from oauth2client.client import GoogleCredentials
from googleapiclient import discovery
from gcloud import bigquery
from gcloud.bigquery import SchemaField
import psycopg2
import datetime

from frontend.models import SHA, PCT, Practice, Measure
from frontend.models import MeasureValue, MeasureGlobal, Chemical
from frontend.management.commands.import_measures import Command
from common import utils


PRESCRIBING_SCHEMA = [
    SchemaField('sha', 'STRING'),
    SchemaField('pct', 'STRING'),
    SchemaField('practice', 'STRING'),
    SchemaField('bnf_code', 'STRING'),
    SchemaField('bnf_name', 'STRING'),
    SchemaField('items', 'INTEGER'),
    SchemaField('net_cost', 'FLOAT'),
    SchemaField('actual_cost', 'FLOAT'),
    SchemaField('quantity', 'INTEGER'),
    SchemaField('month', 'TIMESTAMP'),
]

PRACTICE_SCHEMA = [
   SchemaField('code', 'STRING'),
   SchemaField('name', 'STRING'),
   SchemaField('address1', 'STRING'),
   SchemaField('address2', 'STRING'),
   SchemaField('address3', 'STRING'),
   SchemaField('address4', 'STRING'),
   SchemaField('address5', 'STRING'),
   SchemaField('postcode', 'STRING'),
   SchemaField('location', 'STRING'),
   SchemaField('area_team_id', 'STRING'),
   SchemaField('ccg_id', 'STRING'),
   SchemaField('setting', 'INTEGER'),
   SchemaField('close_date', 'STRING'),
   SchemaField('join_provider_date', 'STRING'),
   SchemaField('leave_provider_date', 'STRING'),
   SchemaField('open_date', 'STRING'),
   SchemaField('status_code', 'STRING'),
 ]


def load_data_from_file(
        dataset_name, table_name,
        source_file_name, schema, _transform=None):
    client = bigquery.Client(project='ebmdatalab')
    dataset = client.dataset(dataset_name)
    table = dataset.table(
        table_name,
        schema=schema)
    if not table.exists():
        table.create()
    table.reload()
    with tempfile.TemporaryFile(mode='rb+') as csv_file:
        with open(source_file_name, 'rb') as source_file:
            writer = csv.writer(csv_file)
            reader = csv.reader(source_file)
            for row in reader:
                if _transform:
                    row = _transform(row)
                writer.writerow(row)
        job = table.upload_from_file(
            csv_file, source_format='text/csv',
            create_disposition="CREATE_IF_NEEDED",
            write_disposition="WRITE_TRUNCATE",
            rewind=True)
        wait_for_job(job)


def load_prescribing_data_from_file(
        dataset_name, table_name, source_file_name):
    def _transform(row):
        # To match the prescribing table format in BigQuery, we have
        # to re-encode the date field as a bigquery TIMESTAMP and drop
        # a couple of columns
        row[10] = "%s 00:00:00" % row[10]
        del(row[3])
        del(row[-1])
        return row
    return load_data_from_file(
        dataset_name, table_name,
        source_file_name, PRESCRIBING_SCHEMA, _transform=_transform)


def load_practice_data(dataset_name, table_name):
    # write the queryset to CSV
    db_name = utils.get_env_setting('DB_NAME')
    db_user = utils.get_env_setting('DB_USER')
    db_pass = utils.get_env_setting('DB_PASS')
    db_host = utils.get_env_setting('DB_HOST', '127.0.0.1')
    conn = psycopg2.connect(database=db_name, user=db_user,
                            password=db_pass, host=db_host)
    with tempfile.NamedTemporaryFile(mode='r+b') as csv_file:
        cols = [x.name for x in PRACTICE_SCHEMA]
        conn.cursor().copy_to(
            csv_file, 'frontend_practice', sep=',', null='', columns=cols)
        csv_file.seek(0)
        load_data_from_file(
            'measures', 'test_practices',
            csv_file.name,
            PRACTICE_SCHEMA
        )
        conn.commit()
        conn.close()


def wait_for_job(job):
    while True:
        job.reload()
        if job.state == 'DONE':
            if job.error_result:
                raise RuntimeError(job.error_result)
            return
        time.sleep(1)


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
        self.assertEqual(result['months'], ['2016-03-01'])


class BehaviourTestCase(TestCase):
    @classmethod
    def setUpClass(cls):
        print "setup", datetime.datetime.now()
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
        print "loading prescribing data", datetime.datetime.now()
        load_prescribing_data_from_file('measures', 'test_data', test_file)
        print "loading practice data", datetime.datetime.now()
        load_practice_data('measures', 'test_practices')
        month = '2015-09-01'
        measure_id = 'cerazette'
        args = []
        opts = {
            'month': month,
            'measure': measure_id,
            'test_mode': True,
            'v': 2
        }
        print "importing data for 2015-09-01", datetime.datetime.now()
        call_command('import_measures', *args, **opts)

        month = '2015-10-01'
        measure_id = 'cerazette'
        args = []
        opts = {
            'month': month,
            'measure': measure_id,
            'test_mode': True,
            'v': 2
        }
        print "importing data for 2015-10-01", datetime.datetime.now()
        call_command('import_measures', *args, **opts)
        print "done", datetime.datetime.now()

    @classmethod
    def tearDownClass(cls):
        call_command('flush', verbosity=0, interactive=False)

    def test_import_measurevalue_by_practice(self):
        print "1", datetime.datetime.now()
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

        # XXX in the new version of the code, we do a left join
        # against practices. In the old version, we effectively do a
        # right join (every practice has an entry).

        # p = Practice.objects.get(code='B82010') # Ripon SPA
        # mv = MeasureValue.objects.get(measure=m, month=month, practice=p)
        # self.assertEqual(mv.numerator, 0)
        # self.assertEqual(mv.denominator, 0)
        # self.assertEqual(mv.percentile, None)
        # self.assertEqual(mv.calc_value, None)
        # self.assertEqual(mv.cost_savings['10'], 0)
        # self.assertEqual(mv.cost_savings['90'], 0)

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

    def test_import_measurevalue_by_practice_with_different_payments(self):
        print "2", datetime.datetime.now()
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
        print "3", datetime.datetime.now()
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
        print "4", datetime.datetime.now()
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
                         'practice']['20'], '65011.21') # XXX here we are 64929.39
        self.assertEqual("%.2f" % mg.cost_savings[
                         'practice']['50'], '59029.41') # here 57838.24
        self.assertEqual("%.2f" % mg.cost_savings[
                         'practice']['70'], '26934.00') # here 10887.00
        self.assertEqual("%.2f" % mg.cost_savings['practice']['90'], '162.00') # here -56259.00
        self.assertEqual("%.2f" % mg.cost_savings['ccg']['10'], '64174.56') # correct
        self.assertEqual("%.2f" % mg.cost_savings['ccg']['30'], '61416.69') # correct
        self.assertEqual("%.2f" % mg.cost_savings['ccg']['50'], '58658.82') # correct
        self.assertEqual("%.2f" % mg.cost_savings['ccg']['80'], '23463.53') # X 19279.47
        self.assertEqual("%.2f" % mg.cost_savings['ccg']['90'], '11731.76') # X 6153.02
