import csv
import datetime
import logging
import os
import time
from google.cloud import storage
from google.cloud import bigquery
from google.cloud.exceptions import NotFound
from google.cloud.bigquery.table import Table
from google.cloud.bigquery.dataset import Dataset

from django.core.management.base import BaseCommand
from django.db import connection

from frontend.management.commands.convert_hscic_prescribing import Command as ConvertCommand
from frontend.models import PCT, ImportLog

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    args = ''
    help = 'Import all data from any data files that have been downloaded. '
    help += 'Set DEBUG to False in your settings before running this.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--filename',
            help=(
                'A path to a properly converted file on the filesystem, '
                'or a URI for a raw file in Google Cloud, e.g. '
                'gs://embdatalab/hscic/'))
        parser.add_argument(
            '--date', help="Specify date rather than infer it from filename")
        parser.add_argument(
            '--skip-orgs',
            action='store_true',
            help="Don't parse orgs from the file")
        parser.add_argument('--truncate')

    def handle(self, *args, **options):
        if options['truncate']:
            self.truncate = True
        else:
            self.truncate = False

        fname = options['filename']
        if options['date']:
            self.date = datetime.datetime.strptime(
                options['date'], '%Y-%m-%d').date()
        else:
            self.date = self._date_from_filename(fname)
        f = self._get_path_to_formatted_data(fname)
        if not options['skip_orgs']:
            self.import_pcts(f)
        self.drop_partition()
        self.create_partition()
        self.import_prescriptions(f)
        self.create_partition_indexes()
        self.add_parent_trigger()
        self.drop_oldest_month()

    def _get_path_to_formatted_data(self, fname):
        if os.path.split(fname)[-1].startswith('T'):
            # Data from HSCIC (which we used to use until we found the
            # more timely version from HSCIC). Convert it to formatted
            # version and return the path to that
            if not fname.endswith('_formatted.CSV'):
                opts = {
                    'verbosity': 0,
                    'filename': fname}
                converted = ConvertCommand().handle(**opts)
                return converted[0]
            else:
                return fname

        else:
            # Data from NHS Digital. This requires aggregating which
            # we do in BigQuery, then download the result for ingestion
            return self.aggregate_nhs_digital_data(fname)

    def import_pcts(self, filename):
        logger.info('Importing SHAs and PCTs from %s' % filename)
        rows = csv.reader(open(filename, 'rU'))
        pct_codes = set()
        i = 0
        for row in rows:
            pct_codes.add(row[0])
            i += 1
            if self.truncate and i > 500:
                break
        pcts_created = 0
        for pct_code in pct_codes:
            p, created = PCT.objects.get_or_create(code=pct_code)
            pcts_created += created
        logger.info("%s PCTs created" % pcts_created)

    def create_partition(self):
        date = self.date
        sql = ("CREATE TABLE %s ("
               "  CHECK ( "
               "    processing_date >= DATE '%s' "
               "      AND processing_date < DATE '%s'"
               "  )"
               ") INHERITS (frontend_prescription);")
        constraint_from = "%s-%s-%s" % (date.year, date.month, "01")
        next_month = (date.month % 12) + 1
        if next_month == 1:
            next_year = date.year + 1
        else:
            next_year = date.year
        constraint_to = "%s-%s-%s" % (
            next_year, str(next_month).zfill(2), "01")
        sql = sql % (
            self._partition_name(),
            constraint_from,
            constraint_to
        )
        with connection.cursor() as cursor:
            cursor.execute(sql)
        logger.info("Created partition %s" % self._partition_name())

    def drop_oldest_month(self):
        five_years_ago = datetime.date(
            self.date.year - 5, self.date.month, self.date.day)
        self.drop_partition(five_years_ago)

    def _partition_name(self, date=None):
        if not date:
            date = self.date
        return "frontend_prescription_%s%s" % (
            date.year, str(date.month).zfill(2))

    def add_parent_trigger(self):
        """A trigger to prevent accidental adding of data to the parent table

        """
        function = ("CREATE OR REPLACE FUNCTION prescription_prevent_action() "
                    "  RETURNS trigger AS $prevent_action$ "
                    "BEGIN "
                    "  RAISE EXCEPTION "
                    "  '% on % not allowed. Perform on descendant tables',"
                    "  TG_OP, TG_TABLE_NAME;"
                    "END; "
                    "$prevent_action$ LANGUAGE plpgsql; ")
        trigger = ("DROP TRIGGER IF EXISTS prevent_action "
                   "  ON frontend_prescription; "
                   "CREATE TRIGGER prevent_action "
                   "BEFORE INSERT OR UPDATE OR DELETE ON frontend_prescription"
                   "  FOR EACH STATEMENT "
                   "  EXECUTE PROCEDURE prescription_prevent_action();")
        with connection.cursor() as cursor:
            cursor.execute(function)
            cursor.execute(trigger)

    def create_partition_indexes(self):
        indexes = [
            ("CREATE INDEX idx_%s_presentation "
             "ON %s (presentation_code varchar_pattern_ops)"),
            ("CREATE INDEX idx_%s_practice_id "
             "ON %s "
             "USING btree (practice_id)"),
            ("CREATE INDEX idx_%s_pct_id "
             "ON %s (pct_id)"),
            ("CREATE INDEX idx_%s_date "
             "ON %s (processing_date)"),
            ("CLUSTER %s USING idx_%s_presentation"),
        ]
        constraints = [
            ("ALTER TABLE %s ADD CONSTRAINT "
             "cnstrt_%s_pkey "
             "PRIMARY KEY (id)"),
            ("ALTER TABLE %s ADD CONSTRAINT "
             "cnstrt_%s__practice_code "
             "FOREIGN KEY (practice_id) REFERENCES frontend_practice(code) "
             "DEFERRABLE INITIALLY DEFERRED"),
            ("ALTER TABLE %s ADD CONSTRAINT "
             "cnstrt_%s__pct_code "
             "FOREIGN KEY (pct_id) REFERENCES frontend_pct(code) "
             "DEFERRABLE INITIALLY DEFERRED"),
            ]
        partition_name = self._partition_name()
        with connection.cursor() as cursor:
            for index_sql in indexes:
                cursor.execute(index_sql % (
                    partition_name, partition_name))
            for constraint_sql in constraints:
                cursor.execute(constraint_sql % (
                    partition_name, partition_name))

    def drop_partition(self, date=None):
        logger.info('Dropping partition %s' % self._partition_name(date=date))
        sql = "DROP TABLE IF EXISTS %s" % self._partition_name(date=date)
        with connection.cursor() as cursor:
            cursor.execute(sql)

    def import_prescriptions(self, filename):
        logger.info('Importing Prescriptions from %s' % filename)
        # start = time.clock()
        copy_str = "COPY %s(pct_id,"
        copy_str += "practice_id,presentation_code,"
        copy_str += "total_items,actual_cost,"
        copy_str += "quantity,processing_date) FROM STDIN "
        copy_str += "WITH (FORMAT CSV)"
        i = 0
        if self.truncate:
            with open("/tmp/sample", "wb") as outfile:
                with open(filename) as infile:
                    for line in infile:
                        outfile.write(line)
                        i += 1
                        if self.truncate and i > 500:
                            break
            file_obj = open("/tmp/sample")
        else:
            file_obj = open(filename)
        with connection.cursor() as cursor:
            cursor.copy_expert(copy_str % self._partition_name(), file_obj)
            ImportLog.objects.create(
                current_at=self.date,
                filename=filename,
                category='prescribing'
            )

    def _date_from_filename(self, filename):
        file_str = filename.replace('T', '').split('/')[-1].split('.')[0]
        return datetime.date(int(file_str[0:4]), int(file_str[4:6]), 1)

    def aggregate_nhs_digital_data(self, fname):
        # Check that something exists at that URI
        client = storage.client.Client(project='ebmdatalab')
        bucket = client.get_bucket("hscic")
        if bucket.get_blob(fname) is None:
            raise NotFound()

        # Set up a temporary data source for the CSV
        uri = bucket.path
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
                "tableId": "raw_nhs_digital_data"
            },
            "externalDataConfiguration": {
                "csvOptions": {
                    "skipLeadingRows": "1"
                },
                "sourceUris": [
                    uri
                ],
                "schema": {"fields": schema}
            }
        }
        client = bigquery.client.Client(project='ebmdatalab')
        dataset = Dataset("tmp_eu", client, project="ebmdatalab")
        table = Table.from_api_repr(resource, dataset)
        table.create()
        # Execute a query against that, writing to another temporary data source
        # That has to be exported to GCS again

        query = """
         SELECT
          BNF_Code AS presentation_code,
          BNF_Description AS presentation_name,
          SUM(Items) AS total_items,
          SUM(Actual_Cost) AS actual_cost,
          SUM(NIC) AS net_cost,
          SUM(Quantity * Items) AS quantity,
          '%s' AS processing_date,
          CASE WHEN BNF_Code LIKE '2%' THEN LEFT(BNF_Code, 4) ELSE LEFT(BNF_Code, 9) END AS chemical_id,
          LEFT(PCO_Code, 3) AS pct_id,
          Practice_Code AS practice_code,
          Area_Team_Code AS sha_id
         FROM [ebmdatalab:tmp_eu.foo]
         GROUP BY presentation_code, presentation_name, pct_id, practice_code, sha_id, chemical_id
         LIMIT 10
        """ % self.date.strftime("%Y-%m-%d")
        dataset = client.dataset('tmp_eu')
        table = dataset.table(
            name='formatted_prescribing_%s' % self.date.strftime("%Y-%m-%d"))
        job = client.run_async_query('create-formatted-table-job', query)
        job.destination = table
        job.begin()
        retry_count = 1000
        while retry_count > 0 and job.state != 'DONE':
            retry_count -= 1
            time.sleep(2)
            job.reload()

        # Download the result
        # Copy to GCS
        destination_path = fname[:-4] + '_formatted.CSV'
        job = client.extract_table_to_storage(
            'extract-formatted-table-job', table,
            "gs://embdatalab/hscic/%s" % destination_path
            )
        job.destination_format = 'CSV'
        job.print_header = False
        retry_count = 1000
        while retry_count > 0 and job.state != 'DONE':
            retry_count -= 1
            time.sleep(2)
            job.reload()

        # Check that something exists at that URI
        client = storage.client.Client(project='ebmdatalab')
        bucket = client.get_bucket('hscic')
        blob = bucket.get_blob(destination_path)
        blob.download_to_filename(destination_path)
        return destination_path
