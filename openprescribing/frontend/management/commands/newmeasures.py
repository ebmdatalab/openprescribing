import time
import re
import os
import datetime
import csv
import json
import glob
import sys

import psycopg2

from oauth2client.client import GoogleCredentials
from googleapiclient import discovery

from django.core.management.base import BaseCommand
from django.db import transaction

from frontend.models import MeasureGlobal
from frontend.models import MeasureValue

from common import utils

PRACTICE_TABLE_NAME = "practice_ratios_%s"
CCG_TABLE_NAME = "ccg_ratios_%s"
GLOBALS_TABLE_NAME = "global_centiles_%s"

class NewMeasures(BaseCommand):
    def __init__(self):
        super(NewMeasures, self).__init__()
        self.fpath = os.path.dirname(__file__)
        credentials = GoogleCredentials.get_application_default()
        self.bigquery = discovery.build('bigquery', 'v2',
                                        credentials=credentials)
        self.parse_measures()

    def drop_internal_cols(self, row, convert=True):
        noise = [
            'denom_denominator',
            'denom_practice',
            'window_size',
            'num_practice',
            'num_numerator',
            'num_month',
            'denom_month',
            'denominator_in_window',
            'numerator_in_window',
            'practice'
        ]
        rename = {
            "month_fmt": "month",
            "practices_ccg": "pct_id",
            "raw_ratio": "calc_value",
            "smoothed_ratio": "smoothed_calc_value",
            "practices_org_code": "practice_id"
        }
        new_row = {}
        for k, v in row.items():
            if convert:
                if k.startswith('ratios_'):
                    k = k[len('ratios_'):]
                if k in rename:
                    k = rename[k]
                if k not in noise:
                    new_row[k] = v
            else:
                new_row[k] = v
        return new_row

    def row_to_dict(self, row, fields):
        dict_row = {}
        for i, item in enumerate(row['f']):
            value = item['v']
            key = fields[i]['name']
            dict_row[key] = value
        return self.drop_internal_cols(dict_row)

    def query_and_return(self, query, table_id, convert=True, legacy=False):
        print query
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
        print "Waiting for job to complete..."
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
                    raise StandardError(
                        json.dumps(response['status']['errors'], indent=2))
                else:
                    print "DONE!"
                    break
        bytes_billed = float(response['statistics']['query']['totalBytesBilled'])
        print "%sGB processed" % (
            round(bytes_billed / 1024 / 1024 / 1024, 2))
        print "Cost $%s" % round(bytes_billed/1e+12 * 5.0, 2)
        return response

    def parse_measures(self):
        self.measures = {}
        files = glob.glob(os.path.join(self.fpath, "./new_measure_definitions/*.json"))
        for fname in files:
            fname = os.path.join(self.fpath, fname)
            json_data = open(fname).read()
            d = json.loads(json_data)
            for k in d:
                if k in self.measures:
                    sys.exit()
                    print "duplicate entry found!", k
                else:
                    self.measures[k] = d[k]

    def get_rows(self, table_name):
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
        while response['rows']: # XXX can we use pageToken instead?
            for row in response['rows']:
                yield self.row_to_dict(row, fields)
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

    def calculate_practice_ratios(self, measure_id, month=None, practice_id=None):
        measure = self.measures[measure_id]
        numerator_where = " ".join(measure['numerator_where'])
        denominator_where = " ".join(measure['denominator_where'])
        if month:
            # validate the format before sending to bigquery
            datetime.datetime.strptime(month, "%Y-%m-%d")
            # Because we smooth using a moving average of three months, we
            # have to filter to a three month window
            date_cond = (
                " AND ("
                "month >= DATE_ADD('{} 00:00:00', -2, 'MONTH') AND "
                "month <= '{} 00:00:00') "
            ).format(month, month)
            numerator_where += date_cond
            denominator_where += date_cond
        if practice_id:
            practice_cond = " AND practice = '{}'".format(practice_id)
            numerator_where += practice_cond
            denominator_where += practice_cond
        numerator_aliases = denominator_aliases = aliased_numerators = aliased_denominators = ''
        for col in self.get_custom_cols(measure_id, 'denominator'):
            denominator_aliases += ", denom.%s AS denom_%s" % (col, col)
            aliased_denominators += ", denom_%s" % col
        for col in self.get_custom_cols(measure_id, 'numerator'):
            numerator_aliases += ", num.%s AS num_%s" % (col, col)
            aliased_numerators += ", num_%s" % col
        sql_path = os.path.join(self.fpath, "./measure_sql/practice_ratios.sql")
        with open(sql_path, "r") as sql_file:
            sql = sql_file.read()
            sql = sql.format(
                numerator_from=measure['numerator_from'],
                numerator_where=numerator_where,
                numerator_columns=" ".join(measure['numerator_columns']),
                denominator_columns=" ".join(measure['denominator_columns']),
                denominator_from=measure['denominator_from'],
                denominator_where=denominator_where,
                numerator_aliases=numerator_aliases,
                denominator_aliases=denominator_aliases,
                aliased_denominators=aliased_denominators,
                aliased_numerators=aliased_numerators
            )
            return self.query_and_return(sql, "practice_ratios_%s" % measure_id)

    def add_percent_rank(self, measure_id, unit=None):
        if unit == 'practice':
            from_table = "ebmdatalab:measures.practice_ratios_%s" % measure_id
            target_table = "practice_ratios_%s" % measure_id
            value_var = 'calc_value' # XXX will want to make this practice in the future
        else:
            from_table = "ebmdatalab:measures.ccg_ratios_%s" % measure_id
            target_table = "ccg_ratios_%s" % measure_id
            value_var = 'calc_value'
        sql_path = os.path.join(self.fpath, "./measure_sql/percent_rank.sql")
        with open(sql_path, "r") as sql_file:
            sql = sql_file.read()
            sql = sql.format(
                from_table=from_table,
                target_table=target_table,
                value_var=value_var)
            return self.query_and_return(sql, target_table, legacy=True)

    def get_custom_cols(self, measure_id, num_or_denom=None):
        assert num_or_denom in ['numerator', 'denominator']
        measure = self.measures[measure_id]
        cols = []
        for col in measure["%s_columns" % num_or_denom]:
            alias = re.search(r"AS ([a-z0-9_]+)", col).group(1)
            if alias != num_or_denom:
                cols.append(alias)
        return cols

    def calculate_global_centiles(self, measure_id, unit='practice'):
        measure = self.measures[measure_id]
        if unit == 'practice':
            sql_path = os.path.join(
                self.fpath, "./measure_sql/global_deciles_practices.sql")
            from_table = "ebmdatalab:measures.practice_ratios_%s" % measure_id
            extra_fields = []
            for col in self.get_custom_cols(measure_id, 'numerator'):
                extra_fields.append("num_" + col)
            for col in self.get_custom_cols(measure_id, 'denominator'):
                extra_fields.append("denom_" + col)
            extra_select_sql = ""
            for f in extra_fields:
                extra_select_sql += ", SUM(%s) as %s" % (f, f)
            if measure["is_cost_based"]:
                extra_select_sql += (
                    ", "
                    "(SUM(denom_cost) - SUM(num_cost)) / (SUM(denom_quantity)"
                    "- SUM(num_quantity)) AS cost_per_denom,"
                    "SUM(num_cost) / SUM(num_quantity) as cost_per_num")
        else:
            extra_fields = []
            for col in self.get_custom_cols(measure_id, 'numerator'):
                extra_fields.append("num_" + col)
            for col in self.get_custom_cols(measure_id, 'denominator'):
                extra_fields.append("denom_" + col)
            extra_select_sql = ""
            for f in extra_fields:
                extra_select_sql += ", practice_deciles.%s as %s" % (f, f)
            if measure["is_cost_based"]:
                extra_select_sql += (
                    ", practice_deciles.cost_per_denom AS cost_per_denom"
                    ", practice_deciles.cost_per_num AS cost_per_num")
            sql_path = os.path.join(
                self.fpath, "./measure_sql/global_deciles_ccgs.sql")
            from_table = "ebmdatalab:measures.ccg_ratios_%s" % measure_id
        with open(sql_path) as sql_file_2:
            value_var = 'calc_value'
            # XXX or practice_calc_value? Presumably no
            sql = sql_file_2.read()
            sql = sql.format(
                from_table=from_table,
                extra_select_sql=extra_select_sql,
                value_var=value_var,
                global_centiles_table="ebmdatalab:measures.global_centiles_%s" % (measure_id)
            )
            # We have to use legacy SQL because there' no
            # PERCENTILE_CONT equivalent in the standard SQL
            self.query_and_return(
                sql, "global_centiles_%s" % (measure_id), legacy=True)

    def calculate_ccg_ratios(self, measure_id, month, practice_id):
        # calculate ratios
        with open(os.path.join(
                self.fpath, "./measure_sql/ccg_ratios.sql")) as sql_file:
            sql = sql_file.read()
            numerator_aliases = denominator_aliases = ''
            for col in self.get_custom_cols(measure_id, 'denominator'):
                denominator_aliases += ", SUM(denom_%s) AS denom_%s" % (col, col)
            for col in self.get_custom_cols(measure_id, 'numerator'):
                numerator_aliases += ", SUM(num_%s) AS num_%s" % (col, col)
            from_table = "ebmdatalab.measures.practice_ratios_%s" % measure_id
            sql = sql.format(denominator_aliases=denominator_aliases,
                             numerator_aliases=numerator_aliases,
                             from_table=from_table)
            self.query_and_return(sql, "ccg_ratios_%s" % measure_id)

    def write_global_centiles_to_database(self, measure_id):
        """Should only get called once for both ccg and practice
        """
        for d in self.get_rows("global_centiles_%s" % (measure_id)):
            ccg_deciles = practice_deciles = {}
            d['measure_id'] = measure_id
            # cast strings to numbers for the after-save hook in
            # the MeasureGlobal model
            for c in [10, 20, 30, 40, 50, 60, 70, 80, 90]:
                ccg_deciles[str(c)] = float(d.pop("practice_%sth" % c))
                practice_deciles[str(c)] = float(d.pop("ccg_%sth" % c))
            mg, created = MeasureGlobal.objects.get_or_create(
                measure=measure_id,
                month=d['month']
            )
            mg.percentiles = {'ccg': ccg_deciles, 'practice': practice_deciles}
            mg.save()
        print "Created %s measureglobals" % c

    def write_ccg_ratios_to_database(self, measure_id):
        with transaction.atomic():
            c = 0
            for datum in self.get_rows("ccg_ratios_%s" % measure_id):
                datum['measure_id'] = measure_id
                cost_savings = {}
                for centile in [10, 20, 30, 40, 50, 60, 70, 80, 90]:
                    cost_savings[str(centile)] = float(datum.pop(
                        "cost_savings_%s" % centile))
                datum['cost_savings'] = cost_savings
                datum['percentile'] = float(datum['percentile']) * 100
                MeasureValue.objects.create(**datum)
                c += 1
        print "Wrote %s CCG measures" % c

    def calculate_cost_savings(self, measure_id, month=None, practice_id=None, unit='practice'):
        # Seems we can overwrite a table that we're querying.
        sql_path = os.path.join(self.fpath, "./measure_sql/cost_savings.sql")
        with open(sql_path, "r") as sql_file:
            sql = sql_file.read()
            if unit == 'practice':
                ratios_table = "ebmdatalab.measures.practice_ratios_%s" % measure_id
                global_table = "ebmdatalab.measures.global_centiles_%s" % measure_id
                target_table = "practice_ratios_%s" % measure_id
            else:
                ratios_table = "ebmdatalab.measures.ccg_ratios_%s" % measure_id
                global_table = "ebmdatalab.measures.global_centiles_%s" % measure_id
                target_table = "ccg_ratios_%s" % measure_id
            sql = sql.format(
                local_table=ratios_table,
                global_table=global_table,
                unit=unit
            )
            self.query_and_return(sql, target_table)

    def write_practice_ratios_to_database(self, measure_id):
        fieldnames = ['pct_id', 'measure_id', 'num_items', 'numerator',
                      'denominator', 'smoothed_calc_value', 'month',
                      'percentile', 'calc_value', 'denom_items',
                      'denom_quantity', 'denom_cost', 'num_cost',
                      'num_quantity', 'practice_id', 'cost_savings']
        with open("/tmp/measures.csv", "w") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            c = 0
            for datum in self.get_rows("practice_ratios_%s" % measure_id):
                datum['measure_id'] = measure_id
                cost_savings = {}
                for centile in [10, 20, 30, 40, 50, 60, 70, 80, 90]:
                    cost_savings[str(centile)] = float(datum.pop(
                        "cost_savings_%s" % centile))
                datum['cost_savings'] = json.dumps(cost_savings)
                datum['percentile'] = float(datum['percentile']) * 100
                writer.writerow(datum)
                c += 1
        print "Commiting data to database...."
        with open("/tmp/measures.csv", "r") as f:
            copy_str = "COPY frontend_measurevalue(%s) FROM STDIN "
            copy_str += "WITH (FORMAT csv)"
            print copy_str % ", ".join(fieldnames)
            self.conn.cursor().copy_expert(copy_str % ", ".join(fieldnames), f)
            self.conn.commit()
        print "Wrote %s values" % c

    def x_write_global_centiles_to_database(self, measure_id):
        # XXX if month specified, only delete that month
        # XXX in transaction?
        with transaction.atomic():
            MeasureGlobal.objects.filter(measure=measure_id).delete()
            c = 0
            print datetime.datetime.now()
            for d in self.get_rows("global_centiles_practice_%s" % measure_id):
                month_practice_deciles = {}
                d['measure_id'] = measure_id
                # cast strings to numbers for the after-save hook in
                # the MeasureGlobal model
                for c in [10, 20, 30, 40, 50, 60, 70, 80, 90]:
                    month_practice_deciles[str(c)] = float(d.pop("p_%sth" % c))
                    d['percentiles'] = {'practice' : month_practice_deciles}
                    c += 1
                    MeasureGlobal.objects.create(**d)
                    print "Wrote %s globals" % c

    def create_practice_measurevalues(self, measure_id, month=None, practice_id=None):
        start = datetime.datetime.now()
        # compute ratios for each pratice, and global centiles
        MeasureValue.objects.filter(measure=measure_id).delete() # XXX not necessarily...
        # 1. work out ratios for each practice
        self.calculate_practice_ratios(measure_id, month, practice_id)
        # 2. Add their percent rank (has to be in a different step to skip nulls)
        self.add_percent_rank(measure_id, unit='practice')
        # 3. calculate global centiles for practices: for each month,
        # what is the median (etc) ratio, plus totals for the various
        # columns
        self.calculate_global_centiles(measure_id, unit='practice')
        # now compute cost savings (updating the per-practice ratio
        # table). This depends on the previous two to run correctly
        # XXX we can skip this step if it's not a cost-saving measure!
        self.calculate_cost_savings(measure_id, month, practice_id)
        self.write_practice_ratios_to_database(measure_id) # XXX with cost savings
        print "%s elapsed" % (datetime.datetime.now() - start)


    def create_ccg_measurevalues(self, measure_id, month=None, practice_id=None):
        """Depends on the practice ratios table having been generated
        (e.g. practice_ratios_cerazette)

        """
        start = datetime.datetime.now()
        # Compute ratios at CCG level
        self.calculate_ccg_ratios(measure_id, month, practice_id)
        self.add_percent_rank(measure_id, unit='ccg')
        # calculate centiles When doing this, we don't want to
        # overwrite the sums, or calc value; we just want to work out the centiles.
        self.calculate_global_centiles(measure_id, unit='ccg')
        self.calculate_cost_savings(measure_id, month, practice_id, unit='ccg')
        self.write_ccg_ratios_to_database(measure_id)
        self.write_global_centiles_to_database(measure_id)
        print "%s elapsed" % (datetime.datetime.now() - start)


class Command(NewMeasures):
    def setUpDb(self):
        db_name = utils.get_env_setting('DB_NAME')
        db_user = utils.get_env_setting('DB_USER')
        db_pass = utils.get_env_setting('DB_PASS')
        db_host = utils.get_env_setting('DB_HOST', '127.0.0.1')
        self.conn = psycopg2.connect(database=db_name, user=db_user,
                                     password=db_pass, host=db_host)

    def handle(self, *args, **options):
        start = datetime.datetime.now()
        self.setUpDb()

        self.create_practice_measurevalues(
            'cerazette')
        self.create_ccg_measurevalues(
            'cerazette')
        print "Total %s elapsed" % (datetime.datetime.now() - start)

# TO generate perfect copy of practices:
# COPY frontend_practice TO '/tmp/practices.csv' DELIMITER ',' CSV HEADER;
# see hscic:practices  in BQ for schema. This will need automatic uploading from runner.py
