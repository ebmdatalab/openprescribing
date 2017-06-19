import csv
import datetime
import glob
import logging
import time

from google.cloud import storage
from google.cloud import bigquery
from google.cloud.exceptions import NotFound
from google.cloud.bigquery.table import Table
from google.cloud.bigquery.dataset import Dataset

from django.core.management.base import BaseCommand
from django.core.management.base import CommandError

from ebmdatalab.bigquery import copy_table_to_gcs
from ebmdatalab.bigquery import download_from_gcs
from ebmdatalab.bigquery import wait_for_job

logger = logging.getLogger(__name__)

TEMP_DATASET = 'tmp_eu'
TEMP_SOURCE_NAME = 'raw_nhs_digital_data'


class Command(BaseCommand):
    """There are two kinds of source we use to generate data.


    The legacy source (the code paths for which, once the new source
    has successfully been imported a few times, can be removed) is
    published erratically; the new "detailed" data source is published
    regularly, each month, so we now prefer that.

    The "detailed" source format has one iine for each presentation
    *and pack size*, so prescriptions of 28 paracetamol will be on a
    separate line from prescriptions of 100 paracetamol.

    The destination format has one line for paracetamol of any pack
    size.

    """
    args = ''
    help = 'Converts HSCIC data files into the format needed for our SQL COPY '
    help += 'statement. We use COPY because it is much faster than INSERT.'

    def add_arguments(self, parser):
        parser.add_argument('--filename')

    def handle(self, *args, **options):
        self.IS_VERBOSE = False
        if options['verbosity'] > 1:
            self.IS_VERBOSE = True

        if 'is_test' in options:
            self.IS_TEST = True
        else:
            self.IS_TEST = False

        if options['filename']:
            filenames = [options['filename']]
        else:
            filenames = glob.glob('./data/raw_data/T*PDPI+BNFT.*')
        converted_filenames = []
        for f in filenames:
            if self.IS_VERBOSE:
                print "--------- Converting %s -----------" % f
            filename_for_output = self.create_filename_for_output_file(f)

            if f.endswith('Detailed_Prescribing_Information.csv'):
                f = f.split('/prescribing/')[1]
                uri = 'gs://ebmdatalab/hscic/prescribing/' + f
                # Grab date from file path
                try:
                    date = datetime.datetime.strptime(
                        uri.split("/")[-2] + "_01", "%Y_%m_%d"
                    ).strftime('%Y_%m_%d')
                except ValueError as e:
                    message = ('The file path must have a YYYY_MM '
                               'date component in the containing directory: ')
                    message += e.message
                    raise CommandError(message)
                converted_filenames.append(
                    self.aggregate_nhs_digital_data(
                        uri, filename_for_output, date))
            else:
                reader = csv.reader(open(f, 'rU'))
                next(reader)
                writer = csv.writer(open(filename_for_output, 'wb'))
                for row in reader:
                    if len(row) == 1:
                        continue
                    data = self.format_row_for_sql_copy(row)
                    writer.writerow(data)
                converted_filenames.append(filename_for_output)
        return ", ".join(converted_filenames)

    def create_filename_for_output_file(self, filename):
        if self.IS_TEST:
            return filename[:-4] + '_test.CSV'
        else:
            return filename[:-4] + '_formatted.CSV'

    def format_row_for_sql_copy(self, row):
        '''
        Transform the data into the format needed for COPY.
        '''
        row = [r.strip() for r in row]
        actual_cost = float(row[7])
        quantity = int(row[8])
        month = row[9]
        formatted_date = '%s-%s-01' % (month[:4], month[4:])
        output = [row[1], row[2], row[3],
                  int(row[5]), float(row[6]), actual_cost,
                  quantity, formatted_date]
        return output

    def aggregate_nhs_digital_data(self, uri, local_path, date):
        """Given a GCS URI for "detailed" prescribing data, run a query to
        aggregate it into the format we use internally, and download
        the resulting data to a `*_formatted.CSV` file, ready for
        importing.

        Returns the path to the formatted file.

        """
        # First, check we can access something at the given URI
        client = storage.client.Client(project='ebmdatalab')
        bucket = client.get_bucket('ebmdatalab')
        path = uri.split('ebmdatalab/')[-1]
        if bucket.get_blob(path) is None:
            # This conversion requires that the file referenced at
            # options['file_name'] has been uploaded as a blob to
            # Google Cloud Services at gs://ebmdatalab/<file_name>
            raise NotFound(path)

        # Create table at raw_nhs_digital_data
        table_ref = create_temporary_data_source(uri)
        self.append_aggregated_data_to_prescribing_table(
            table_ref, date)
        temp_table = self.write_aggregated_data_to_temp_table(
            table_ref, date)
        converted_uri = uri[:-4] + '_formatted-*.csv.gz'
        copy_table_to_gcs(temp_table, converted_uri)
        return download_from_gcs(converted_uri, local_path)

    def assert_latest_data_not_already_uploaded(self, date):
        client = bigquery.client.Client(project='ebmdatalab')
        sql = """SELECT COUNT(*)
        FROM [ebmdatalab:hscic.prescribing]
        WHERE month = TIMESTAMP('%s')""" % date.replace('_', '-')
        query = client.run_sync_query(sql)
        query.run()
        assert query.rows[0][0] == 0

    def append_aggregated_data_to_prescribing_table(
            self, source_table_ref, date):
        self.assert_latest_data_not_already_uploaded(date)
        client = bigquery.client.Client(project='ebmdatalab')
        query = """
         SELECT
          Area_Team_Code AS sha,
          LEFT(PCO_Code, 3) AS pct,
          Practice_Code AS practice,
          BNF_Code AS bnf_code,
          BNF_Description AS bnf_name,
          SUM(Items) AS items,
          SUM(NIC) AS net_cost,
          SUM(Actual_Cost) AS actual_cost,
          SUM(Quantity * Items) AS quantity,
          TIMESTAMP('%s') AS month,
         FROM %s
         WHERE Practice_Code NOT LIKE '%%998'  -- see issue #349
         GROUP BY
           bnf_code, bnf_name, pct,
           practice, sha
        """ % (date.replace('_', '-'), source_table_ref)
        dataset = client.dataset('hscic')
        table = dataset.table(
            name='prescribing')
        job = client.run_async_query("create_%s_%s" % (
            table.name, int(time.time())), query)
        job.destination = table
        job.use_query_cache = False
        job.write_disposition = 'WRITE_APPEND'
        job.allow_large_results = True
        wait_for_job(job)
        return table

    def write_aggregated_data_to_temp_table(
            self, source_table_ref, date):
        query = """
         SELECT
          LEFT(PCO_Code, 3) AS pct_id,
          Practice_Code AS practice_code,
          BNF_Code AS presentation_code,
          SUM(Items) AS total_items,
          SUM(Actual_Cost) AS actual_cost,
          SUM(Quantity * Items) AS quantity,
          '%s' AS processing_date,
         FROM %s
         WHERE Practice_Code NOT LIKE '%%998'  -- see issue #349
         GROUP BY
           presentation_code, pct_id, practice_code
        """ % (date, source_table_ref)
        client = bigquery.client.Client(project='ebmdatalab')
        dataset = client.dataset(TEMP_DATASET)
        table = dataset.table(
            name='formatted_prescribing_%s' % date)
        job = client.run_async_query("create_%s_%s" % (
            table.name, int(time.time())), query)
        job.destination = table
        job.use_query_cache = False
        job.write_disposition = 'WRITE_TRUNCATE'
        job.allow_large_results = True
        wait_for_job(job)
        return table


def create_temporary_data_source(source_uri):
    """Create a temporary data source so BigQuery can query the CSV in
    Google Cloud Storage.

    Nothing like this is currently implemented in the
    google-cloud-python library.

    Returns a table reference suitable for using in a BigQuery SQL
    query (legacy format).

    """
    schema = [
        {"name": "Regional_Office_Name", "type": "string"},
        {"name": "Regional_Office_Code", "type": "string"},
        {"name": "Area_Team_Name", "type": "string"},
        {"name": "Area_Team_Code", "type": "string", "mode": "required"},
        {"name": "PCO_Name", "type": "string"},
        {"name": "PCO_Code", "type": "string"},
        {"name": "Practice_Name", "type": "string"},
        {"name": "Practice_Code", "type": "string", "mode": "required"},
        {"name": "BNF_Code", "type": "string", "mode": "required"},
        {"name": "BNF_Description", "type": "string", "mode": "required"},
        {"name": "Items", "type": "integer", "mode": "required"},
        {"name": "Quantity", "type": "integer", "mode": "required"},
        {"name": "ADQ_Usage", "type": "float"},
        {"name": "NIC", "type": "float", "mode": "required"},
        {"name": "Actual_Cost", "type": "float", "mode": "required"},
    ]
    resource = {
        "tableReference": {
            "tableId": TEMP_SOURCE_NAME
        },
        "externalDataConfiguration": {
            "csvOptions": {
                "skipLeadingRows": "1"
            },
            "sourceFormat": "CSV",
            "sourceUris": [
                source_uri
            ],
            "schema": {"fields": schema}
        }
    }
    client = bigquery.client.Client(project='ebmdatalab')
    # delete the table if it exists
    dataset = Dataset("tmp_eu", client)
    table = Table.from_api_repr(resource, dataset)
    try:
        table.delete()
    except NotFound:
        pass
    # Now create it
    path = "/projects/ebmdatalab/datasets/%s/tables" % TEMP_DATASET
    client._connection.api_request(
        method='POST', path=path, data=resource)
    return "[ebmdatalab:%s.%s]" % (TEMP_DATASET, TEMP_SOURCE_NAME)
