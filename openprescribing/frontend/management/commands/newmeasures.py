import time
import re
import os
import datetime
from oauth2client.client import GoogleCredentials
from googleapiclient import discovery
from django.db import transaction
from django.core.management.base import BaseCommand
import json
import glob
import sys

from frontend.models import Measure, MeasureGlobal
from frontend.models import MeasureValue, Practice, PCT


class NewMeasures(object):
    def __init__(self):
        super(NewMeasures, self).__init__()
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

    def query_and_return(self, query, table_id, convert=True):
        print query
        payload = {
            "configuration": {
                "query": {
                    "query": query,
                    "flattenResuts": False,
                    "allowLargeResults": True,
                    "timeoutMs": 100000,
                    "useQueryCache": True,
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
        fpath = os.path.dirname(__file__)
        files = glob.glob(os.path.join(fpath, "./new_measure_definitions/*.json"))
        for fname in files:
            fname = os.path.join(fpath, fname)
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

    def calculate_smoothed_ratios(self, measure_id, month=None, practice_id=None):
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
        fpath = os.path.dirname(__file__)
        sql_path = os.path.join(fpath, "./measure_sql/smoothed_ratios.sql")
        with open(sql_path, "r") as sql_file:
            sql = sql_file.read()
            sql = sql.format(
                numerator_from=measure['numerator_from'],
                numerator_where=numerator_where,
                numerator_columns=" ".join(measure['numerator_columns']),
                denominator_columns=" ".join(measure['denominator_columns']),
                denominator_from=measure['denominator_from'],
                denominator_where=denominator_where
            )
            return self.query_and_return(sql, "smoothed_ratios_%s" % measure_id)

    def calculate_global_centiles(self, measure_id):
        measure = self.measures[measure_id]
        extra_fields = []

        for col in measure['numerator_columns']:
            alias = re.search(r"AS ([a-z0-9_]+)", col).group(1)
            if alias not in ["numerator", "denominator"]:
                extra_fields.append("ratios_num_" + alias)
        for col in measure['denominator_columns']:
            alias = re.search(r"AS ([a-z0-9_]+)", col).group(1)
            if alias not in ["numerator", "denominator"]:
                extra_fields.append("ratios_denom_" + alias)
        extra_select_sql = ""
        for f in extra_fields:
            extra_select_sql += ", SUM(%s) as %s" % (f, f)
        if measure["is_cost_based"]:
            extra_select_sql += """,
SUM(ratios_denom_cost) / SUM(ratios_denom_quantity) AS cost_per_denom,
SUM(ratios_num_cost) / SUM(ratios_num_quantity) as cost_per_num
"""

        fpath = os.path.dirname(__file__)
        with open(os.path.join(fpath, "./measure_sql/global_deciles.sql")) as sql_file_2:
            sql = sql_file_2.read()
            sql = sql.format(
                from_table="[measures.smoothed_ratios_%s]" % measure_id,
                extra_select_sql=extra_select_sql)
            return self.query_and_return(sql, "global_centiles_%s" % measure_id)

    def create_practice_measurevalues(self, measure_id, month=None, practice_id=None):
        # See
        # http://stackoverflow.com/questions/17267417/how-to-upsert-merge-insert-on-duplicate-update-in-postgresql
        # Note when we upgrade to postgres 9.5 we can use `INSERT
        # ... ON CONFLICT UPDATE`
        start = datetime.datetime.now()
        with transaction.atomic():
            MeasureValue.objects.filter(measure=measure_id).delete()
            ratios = self.calculate_smoothed_ratios(measure_id, month, practice_id)
            deciles = self.calculate_global_centiles(measure_id)
            c = 0
            for datum in self.get_rows("smoothed_ratios_%s" % measure_id):
                datum['measure_id'] = measure_id
                MeasureValue.objects.create(**datum)
                c += 1
                if c % 1000 == 0:
                    print ".",
            print "Created %s measurevalues" % c
            MeasureGlobal.objects.filter(measure=measure_id).delete()
            c = 0
            for d in self.get_rows("global_centiles_%s" % measure_id):
                month_practice_deciles = {}
                d['measure_id'] = measure_id
                # cast strings to numbers for the after-save hook in
                # the MeasureGlobal model
                for c in [10, 20, 30, 40, 50, 60, 70, 80, 90]:
                    month_practice_deciles[str(c)] = float(d.pop("p_%sth" % c))
                d['percentiles'] = {'practice' : month_practice_deciles}
                c += 1
                MeasureGlobal.objects.create(**d)
            print "Created %s measureglobals" % c

        print "%s elapsed" % (datetime.datetime.now() - start)


class Command(BaseCommand):
    def handle(self, *args, **options):
        NewMeasures().create_practice_measurevalues(
            'cerazette', practice_id='A81032')
