import datetime
import logging

from django.conf import settings
from django.core.management.base import BaseCommand
from django.core.management.base import CommandError

from ebmdatalab.bigquery import Client, TableExporter

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
        self.IS_VERBOSE = (options['verbosity'] > 1)

        if 'is_test' in options:
            self.IS_TEST = True
        else:
            self.IS_TEST = False

        filename = options['filename']

        if self.IS_VERBOSE:
            print "--------- Converting %s -----------" % filename

        filename_for_output = self.create_filename_for_output_file(filename)

        filename = filename.split('/prescribing/')[1]
        uri = 'gs://ebmdatalab/hscic/prescribing/' + filename
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

        self.aggregate_nhs_digital_data(uri, filename_for_output, date)

    def create_filename_for_output_file(self, filename):
        if self.IS_TEST:
            return filename[:-4] + '_test.CSV'
        else:
            return filename[:-4] + '_formatted.CSV'

    def aggregate_nhs_digital_data(self, uri, local_path, date):
        """Given a GCS URI for "detailed" prescribing data, run a query to
        aggregate it into the format we use internally, and download
        the resulting data to a `*_formatted.CSV` file, ready for
        importing.
        """
        # Create table at raw_nhs_digital_data
        gcs_path = uri.split('ebmdatalab/')[1]
        raw_data_table = get_or_create_raw_data_table(gcs_path)

        self.append_aggregated_data_to_prescribing_table(
            raw_data_table.legacy_full_qualified_name, date)
        temp_table = self.write_aggregated_data_to_temp_table(
            raw_data_table.legacy_full_qualified_name, date)

        exporter = TableExporter(temp_table, gcs_path + '_formatted-')
        exporter.export_to_storage(print_header=False)
        with open(local_path, 'w') as f:
            exporter.download_from_storage_and_unzip(f)

    def assert_latest_data_not_already_uploaded(self, date):
        client = Client(settings.BQ_HSCIC_DATASET)
        sql = """SELECT COUNT(*)
        FROM [ebmdatalab:hscic.prescribing]
        WHERE month = TIMESTAMP('%s')""" % date.replace('_', '-')
        results = client.query(sql)
        assert query.rows[0][0] == 0

    def append_aggregated_data_to_prescribing_table(
            self, raw_data_table_name, date):
        self.assert_latest_data_not_already_uploaded(date)

        client = Client(settings.BQ_HSCIC_DATASET)
        table = client.get_table_ref('prescribing')

        sql = """
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
        """ % (date.replace('_', '-'), raw_data_table_name)
        table.insert_rows_from_query(
            sql,
            legacy=True,
            write_disposition='WRITE_APPEND'
        )

    def write_aggregated_data_to_temp_table(
            self, raw_data_table_name, date):
        sql = """
         SELECT
          LEFT(PCO_Code, 3) AS pct_id,
          Practice_Code AS practice_code,
          BNF_Code AS presentation_code,
          SUM(Items) AS total_items,
          SUM(NIC) AS net_cost,
          SUM(Actual_Cost) AS actual_cost,
          SUM(Quantity * Items) AS quantity,
          '%s' AS processing_date,
         FROM %s
         WHERE Practice_Code NOT LIKE '%%998'  -- see issue #349
         GROUP BY
           presentation_code, pct_id, practice_code
        """ % (date, raw_data_table_name)

        client = Client(TEMP_DATASET)
        table = client.get_table_ref('formatted_prescribing_%s' % date)
        table.insert_rows_from_query(sql, legacy=True)
        return table


def get_or_create_raw_data_table(gcs_path):
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
    client = Client(TEMP_DATASET)
    table = client.get_or_create_storage_backed_table(
        TEMP_SOURCE_NAME,
        schema,
        gcs_path
    )
    return table
