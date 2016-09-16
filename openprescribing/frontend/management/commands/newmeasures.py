import time
import re
import os
import datetime
import csv
import json
import glob
import sys
import tempfile

import psycopg2

from oauth2client.client import GoogleCredentials
from googleapiclient import discovery

from django.core.management.base import BaseCommand
from django.db import transaction

from frontend.models import MeasureGlobal
from frontend.models import MeasureValue

from common import utils

BG_PROJECT = 'ebmdatalab'
BG_DATASET = 'measures'
PRACTICE_TABLE_PREFIX = "practice_data"
CCG_TABLE_PREFIX = "ccg_data"
GLOBALS_TABLE_PREFIX = "global_data"


class MeasureCalculation(object):
    def __init__(self, measure_id, practice_id=None, month=None):
        self.fpath = os.path.dirname(__file__)
        credentials = GoogleCredentials.get_application_default()
        self.bigquery = discovery.build('bigquery', 'v2',
                                        credentials=credentials)
        self.measure = self.parse_measures()[measure_id]
        self.measure_id = measure_id
        self.month = month
        self.practice_id = practice_id
        self.setUpDb()

    def setUpDb(self):
        db_name = utils.get_env_setting('DB_NAME')
        db_user = utils.get_env_setting('DB_USER')
        db_pass = utils.get_env_setting('DB_PASS')
        db_host = utils.get_env_setting('DB_HOST', '127.0.0.1')
        self.conn = psycopg2.connect(database=db_name, user=db_user,
                                     password=db_pass, host=db_host)

    def parse_measures(self):
        """Deserialise JSON measures definition
        """
        measures = {}
        files = glob.glob(os.path.join(self.fpath, "./new_measure_definitions/*.json"))
        for fname in files:
            fname = os.path.join(self.fpath, fname)
            json_data = open(fname).read()
            d = json.loads(json_data)
            for k in d:
                if k in measures:
                    sys.exit()
                    print "duplicate entry found!", k
                else:
                    measures[k] = d[k]
        return measures

    def _get_custom_cols(self, num_or_denom=None):
        """Return column names referred to in measure definitions for either
        numerator or denominator

        """

        assert num_or_denom in ['numerator', 'denominator']
        cols = []
        for col in self.measure["%s_columns" % num_or_denom]:
            alias = re.search(r"AS ([a-z0-9_]+)", col).group(1)
            if alias != num_or_denom:
                cols.append(alias)
        return cols

    def _row_to_dict(self, row, fields):
        """Converts a row from bigquery into a dictionary
        """
        dict_row = {}
        for i, item in enumerate(row['f']):
            value = item['v']
            key = fields[i]['name']
            dict_row[key] = value
        return dict_row

    def query_and_return(self, query, table_id, convert=True, legacy=False):
        """Send query to BigQuery, wait, and return response object when the
        job has completed.

        """
        if not legacy:
            query = query.replace(
                "%s:%s" % (BG_PROJECT, BG_DATASET),
                "%s.%s" % (BG_PROJECT, BG_DATASET))
        payload = {
            "configuration": {
                "query": {
                    "query": query,
                    "flattenResuts": False,
                    "allowLargeResults": True,
                    "timeoutMs": 100000,
                    "useQueryCache": True,
                    "useLegacySql": legacy,
                    "destinationTable": {
                        "projectId": 'ebmdatalab',
                        "tableId": table_id,
                        "datasetId": 'measures'
                    },
                    "createDisposition": "CREATE_IF_NEEDED",
                    "writeDisposition": "WRITE_TRUNCATE"
                }
            }
        }
        response = self.bigquery.jobs().insert(
            projectId='ebmdatalab',
            body=payload).execute()
        print "Waiting for bigquery job to complete..."
        counter = 0
        job_id = response['jobReference']['jobId']
        while True:
            time.sleep(1)
            if counter % 5 == 0:
                sys.stdout.write(".")
                sys.stdout.flush()
            response = self.bigquery.jobs().get(
                projectId='ebmdatalab',
                jobId=job_id).execute()
            counter += 1
            if response['status']['state'] == 'DONE':
                if 'errors' in response['status']:
                    print json.dumps(response, indent=2)
                    raise StandardError(
                        json.dumps(response['status']['errors'], indent=2))
                else:
                    print "done!"
                    break
        bytes_billed = float(response['statistics']['query']['totalBytesBilled'])
        gb_processed = round(bytes_billed / 1024 / 1024 / 1024, 2)
        est_cost = round(bytes_billed/1e+12 * 5.0, 2)
        # Add our own metadata
        print "Cost: %s" % est_cost
        response['openp'] = {'query': query,
                             'est_cost': est_cost,
                             'gb_processed': gb_processed}
        return response

    def get_rows(self, table_name):
        """Iterate over the specified bigquery table, returning a dict for
        each row of data.

        """
        fields = self.bigquery.tables().get(
            projectId='ebmdatalab',
            datasetId='measures',
            tableId=table_name
        ).execute()['schema']['fields']
        response = self.bigquery.tabledata().list(
            projectId='ebmdatalab',
            datasetId='measures',
            tableId=table_name,
            maxResults=100000, startIndex=0).execute()
        while response['rows']:
            for row in response['rows']:
                yield self._row_to_dict(row, fields)
            if 'pageToken' in response:
                response = self.bigquery.tabledata().list(
                    projectId='ebmdatalab',
                    datasetId='measures',
                    tableId=table_name,
                    pageToken=response['pageToken'],
                    maxResults=100000).execute()
            else:
                break
        raise StopIteration

    def add_percent_rank(self):
        from_table = self.full_table_name()
        target_table = self.table_name()
        value_var = 'calc_value' # XXX will want to make this
        # smoothed_calc_value in the
        # future
        sql_path = os.path.join(self.fpath, "./measure_sql/percent_rank.sql")
        with open(sql_path, "r") as sql_file:
            sql = sql_file.read()
            sql = sql.format(
                from_table=from_table,
                target_table=target_table,
                value_var=value_var)
            return self.query_and_return(sql, target_table, legacy=True)

    def write_global_centiles_to_database(self):
        """XXX Should only get called once for both ccg and practice
        """
        for d in self.get_rows(self.globals_table_name()):
            ccg_deciles = practice_deciles = {}
            d['measure_id'] = self.measure_id
            # cast strings to numbers for the after-save hook in
            # the MeasureGlobal model
            for c in [10, 20, 30, 40, 50, 60, 70, 80, 90]:
                ccg_deciles[str(c)] = float(d.pop("practice_%sth" % c))
                practice_deciles[str(c)] = float(d.pop("ccg_%sth" % c))
            mg, created = MeasureGlobal.objects.get_or_create(
                measure=self.measure_id,
                month=d['month']
            )
            mg.percentiles = {'ccg': ccg_deciles, 'practice': practice_deciles}
            mg.save()
        print "Created %s measureglobals" % c

    def _query_and_write_global_centiles(self,
                                         sql_path,
                                         value_var,
                                         from_table,
                                         extra_select_sql):

        with open(sql_path) as sql_file:
            value_var = 'calc_value'
            sql = sql_file.read()
            sql = sql.format(
                from_table=from_table,
                extra_select_sql=extra_select_sql,
                value_var=value_var,
                global_centiles_table=self.full_globals_table_name())
            # We have to use legacy SQL because there' no
            # PERCENTILE_CONT equivalent in the standard SQL
            return self.query_and_return(
                sql, self.globals_table_name(), legacy=True)

    def full_table_name(self):
        return "%s:%s.%s" % (BG_PROJECT, BG_DATASET, self.table_name())

    def globals_table_name(self):
        return "%s_%s" % (GLOBALS_TABLE_PREFIX, self.measure_id)

    def full_globals_table_name(self):
        return "%s:%s.%s" % (BG_PROJECT, BG_DATASET, self.globals_table_name())


class PracticeCalculation(MeasureCalculation):
    def table_name(self):
        return "%s_%s" % (PRACTICE_TABLE_PREFIX, self.measure_id)

    def calculate_practice_ratios(self):
        numerator_where = " ".join(self.measure['numerator_where'])
        denominator_where = " ".join(self.measure['denominator_where'])
        if self.month:
            # validate the format before sending to bigquery
            datetime.datetime.strptime(self.month, "%Y-%m-%d")
            # Because we smooth using a moving average of three months, we
            # have to filter to a three month window
            date_cond = (
                " AND ("
                "month >= DATE_ADD('{} 00:00:00', -2, 'MONTH') AND "
                "month <= '{} 00:00:00') "
            ).format(self.month, self.month)
            numerator_where += date_cond
            denominator_where += date_cond
        if self.practice_id:
            practice_cond = " AND practice = '{}'".format(self.practice_id)
            numerator_where += practice_cond
            denominator_where += practice_cond
        numerator_aliases = denominator_aliases = aliased_numerators = aliased_denominators = ''
        for col in self._get_custom_cols('denominator'):
            denominator_aliases += ", denom.%s AS denom_%s" % (col, col)
            aliased_denominators += ", denom_%s" % col
        for col in self._get_custom_cols('numerator'):
            numerator_aliases += ", num.%s AS num_%s" % (col, col)
            aliased_numerators += ", num_%s" % col
        sql_path = os.path.join(self.fpath, "./measure_sql/practice_ratios.sql")
        with open(sql_path, "r") as sql_file:
            sql = sql_file.read()
            sql = sql.format(
                numerator_from=self.measure['numerator_from'],
                numerator_where=numerator_where,
                numerator_columns=" ".join(self.measure['numerator_columns']),
                denominator_columns=" ".join(self.measure['denominator_columns']),
                denominator_from=self.measure['denominator_from'],
                denominator_where=denominator_where,
                numerator_aliases=numerator_aliases,
                denominator_aliases=denominator_aliases,
                aliased_denominators=aliased_denominators,
                aliased_numerators=aliased_numerators
            )
            return self.query_and_return(sql, self.table_name())

    def calculate_global_centiles(self):
        sql_path = os.path.join(
            self.fpath, "./measure_sql/global_deciles_practices.sql")
        from_table = self.full_table_name()
        extra_fields = []
        for col in self._get_custom_cols('numerator'):
            extra_fields.append("num_" + col)
        for col in self._get_custom_cols('denominator'):
            extra_fields.append("denom_" + col)
        extra_select_sql = ""
        for f in extra_fields:
            extra_select_sql += ", SUM(%s) as %s" % (f, f)
        if self.measure["is_cost_based"]:
            extra_select_sql += (
                ", "
                "(SUM(denom_cost) - SUM(num_cost)) / (SUM(denom_quantity)"
                "- SUM(num_quantity)) AS cost_per_denom,"
                "SUM(num_cost) / SUM(num_quantity) as cost_per_num")
        value_var = 'calc_value'  # could be smoothed_calc_value in future
        return self._query_and_write_global_centiles(
            sql_path, value_var, from_table, extra_select_sql)

    def calculate_cost_savings(self):
        """Appends cost savings column to the Practice ratios table"""
        sql_path = os.path.join(self.fpath, "./measure_sql/cost_savings.sql")
        with open(sql_path, "r") as sql_file:
            sql = sql_file.read()
            ratios_table = self.full_table_name()
            global_table = self.full_globals_table_name()
            target_table = self.table_name()
            sql = sql.format(
                local_table=ratios_table,
                global_table=global_table,
                unit='practice'
            )
            self.query_and_return(sql, target_table)

    def write_practice_ratios_to_database(self):
        """Copies the bigquery ratios data to the local postgres database.
        Uses COPY command via a CSV file for performance.
        """
        fieldnames = ['pct_id', 'measure_id', 'num_items', 'numerator',
                      'denominator', 'smoothed_calc_value', 'month',
                      'percentile', 'calc_value', 'denom_items',
                      'denom_quantity', 'denom_cost', 'num_cost',
                      'num_quantity', 'practice_id', 'cost_savings']
        f = tempfile.TemporaryFile(mode='r+')
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        c = 0
        for datum in self.get_rows(self.table_name()):
            datum['measure_id'] = self.measure_id
            cost_savings = {}
            for centile in [10, 20, 30, 40, 50, 60, 70, 80, 90]:
                cost_savings[str(centile)] = float(datum.pop(
                    "cost_savings_%s" % centile))
            datum['cost_savings'] = json.dumps(cost_savings)
            datum['percentile'] = float(datum['percentile']) * 100
            writer.writerow(datum)
            c += 1
        print "Commiting data to database...."
        copy_str = "COPY frontend_measurevalue(%s) FROM STDIN "
        copy_str += "WITH (FORMAT csv)"
        print copy_str % ", ".join(fieldnames)
        f.seek(0)
        self.conn.cursor().copy_expert(copy_str % ", ".join(fieldnames), f)
        self.conn.commit()
        f.close()
        print "Wrote %s values" % c


class CCGCalculation(MeasureCalculation):
    def table_name(self):
        return "%s_%s" % (CCG_TABLE_PREFIX, self.measure_id)

    def calculate_ccg_ratios(self):
        """Sums all the fields in the per-practice table, grouped by
        CCG. Stores in a new table.
        """
        with open(os.path.join(
                self.fpath, "./measure_sql/ccg_ratios.sql")) as sql_file:
            sql = sql_file.read()
            numerator_aliases = denominator_aliases = ''
            for col in self._get_custom_cols('denominator'):
                denominator_aliases += ", SUM(denom_%s) AS denom_%s" % (col, col)
            for col in self._get_custom_cols('numerator'):
                numerator_aliases += ", SUM(num_%s) AS num_%s" % (col, col)
            from_table = PracticeCalculation(self.measure_id).full_table_name()
            sql = sql.format(denominator_aliases=denominator_aliases,
                             numerator_aliases=numerator_aliases,
                             from_table=from_table)
            self.query_and_return(sql, self.table_name())

    def calculate_global_centiles(self):
        extra_fields = []
        for col in self._get_custom_cols('numerator'):
            extra_fields.append("num_" + col)
        for col in self._get_custom_cols('denominator'):
            extra_fields.append("denom_" + col)
        extra_select_sql = ""
        for f in extra_fields:
            extra_select_sql += ", practice_deciles.%s as %s" % (f, f)
        if self.measure["is_cost_based"]:
            extra_select_sql += (
                ", practice_deciles.cost_per_denom AS cost_per_denom"
                ", practice_deciles.cost_per_num AS cost_per_num")
        sql_path = os.path.join(
            self.fpath, "./measure_sql/global_deciles_ccgs.sql")
        from_table = self.full_table_name()
        value_var = 'calc_value'  # could be smoothed_calc_value in future
        return self._query_and_write_global_centiles(
            sql_path, value_var, from_table, extra_select_sql)

    def write_ccg_ratios_to_database(self):
        with transaction.atomic():
            c = 0
            for datum in self.get_rows(self.table_name()):
                datum['measure_id'] = self.measure_id
                cost_savings = {}
                for centile in [10, 20, 30, 40, 50, 60, 70, 80, 90]:
                    cost_savings[str(centile)] = float(datum.pop(
                        "cost_savings_%s" % centile))
                datum['cost_savings'] = cost_savings
                datum['percentile'] = float(datum['percentile']) * 100
                MeasureValue.objects.create(**datum)
                c += 1
        print "Wrote %s CCG measures" % c

    def calculate_cost_savings(self):
        """Appends cost savings column to the CCG ratios table"""

        sql_path = os.path.join(self.fpath, "./measure_sql/cost_savings.sql")
        with open(sql_path, "r") as sql_file:
            sql = sql_file.read()
            ratios_table = self.full_table_name()
            global_table = self.full_globals_table_name()
            target_table = self.table_name()
            sql = sql.format(
                local_table=ratios_table,
                global_table=global_table,
                unit='ccg'
            )
            self.query_and_return(sql, target_table)

# XXX why do we see CCGs like 5EM which don't

class Command(BaseCommand):
    def handle(self, *args, **options):
        start = datetime.datetime.now()
        self.create_practice_measurevalues('cerazette')
        self.create_ccg_measurevalues('cerazette')
        print "Total %s elapsed" % (datetime.datetime.now() - start)

    def create_practice_measurevalues(
            self, measure_id, month=None, practice_id=None):
        start = datetime.datetime.now()
        # compute ratios for each pratice, and global centiles
        # XXX not necessarily... when do we want to delete measures?
        MeasureValue.objects.filter(measure=measure_id).delete()
        calc = PracticeCalculation(measure_id)
        calc.calculate_practice_ratios()
        calc.add_percent_rank()
        calc.calculate_global_centiles()
        # now compute cost savings (updating the per-practice ratio
        # table). This depends on the previous two to run correctly
        # XXX we can skip this step if it's not a cost-saving measure!
        if calc.measure['is_cost_based']:
            calc.calculate_cost_savings()
        calc.write_practice_ratios_to_database()
        print "%s elapsed" % (datetime.datetime.now() - start)


    def create_ccg_measurevalues(
            self, measure_id, month=None, practice_id=None):
        """Depends on the practice ratios table having been generated
        (e.g. practice_ratios_cerazette)

        """
        start = datetime.datetime.now()
        # Compute ratios at CCG level
        calc = CCGCalculation(measure_id)
        calc.calculate_ccg_ratios()
        calc.add_percent_rank()
        # calculate centiles When doing this, we don't want to
        # overwrite the sums, or calc value; we just want to work out the centiles.
        calc.calculate_global_centiles()
        if calc.measure['is_cost_based']:
            calc.calculate_cost_savings()
        calc.write_ccg_ratios_to_database()
        # XXX note we only write the global centiles after we've
        # computed both the practice and ccg global centiles
        calc.write_global_centiles_to_database()
        print "%s elapsed" % (datetime.datetime.now() - start)

# TO generate perfect copy of practices:
# COPY frontend_practice TO '/tmp/practices.csv' DELIMITER ',' CSV HEADER;
# see hscic:practices  in BQ for schema. This will need automatic uploading from runner.py
