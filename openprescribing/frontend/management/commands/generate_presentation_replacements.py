import csv
import glob
import logging
import re
import tempfile
import time

from django.core.management.base import BaseCommand
from django.core.management.base import CommandError
from django.db import connection
from django.db import transaction

from google.cloud.bigquery import SchemaField
from google.cloud import bigquery
from google.cloud.bigquery.dataset import Dataset
from google.cloud.exceptions import Conflict

from frontend.models import Chemical
from frontend.models import Presentation
from frontend.models import Product
from frontend.models import Section

from ebmdatalab.bigquery import load_data_from_file
from ebmdatalab.bigquery import copy_table_to_gcs
from ebmdatalab.bigquery import download_from_gcs
from ebmdatalab.bigquery import wait_for_job


logger = logging.getLogger(__name__)


BNF_MAP_SCHEMA = [
    SchemaField('former_bnf_code', 'STRING'),
    SchemaField('current_bnf_code', 'STRING'),
]


def create_code_mapping(filenames):
    Presentation.objects.filter(replaced_by__isnull=False).delete()
    for f in filenames:
        with transaction.atomic():
            for line in open(f, 'r'):
                if not line.strip():
                    continue  # skip blank lines
                if "\t" not in line:
                    raise CommandError(
                        "Input lines must be tab delimited: %s" % line)
                prev_code, next_code = line.split("\t")
                prev_code = prev_code.strip()
                next_code = next_code.strip()

                if len(prev_code) <= 7:  # section, subsection, paragraph
                    Section.objects.filter(
                        bnf_id__startswith=prev_code).update(
                            is_current=False)
                elif len(prev_code) == 9:
                    Chemical.objects.filter(
                        bnf_code=prev_code).update(is_current=False)
                elif len(prev_code) == 11:
                    Product.objects.filter(
                        bnf_code=prev_code).update(is_current=False)

                if re.match(r'^[0-9A-Z]+$', next_code):  # Skip 'withdrawn' &c
                    matches = Presentation.objects.filter(
                        bnf_code__startswith=next_code)
                    for row in matches:
                        replaced_by_id = row.pk
                        row.pk = None  # allows us to clone
                        row.replaced_by_id = replaced_by_id
                        row.bnf_code = (
                            prev_code + replaced_by_id[len(prev_code):])
                        row.save()


def create_bigquery_table():
    dataset_name = 'hscic'
    bq_table_name = 'bnf_map'
    # output a row for each presentation and its ultimate replacement
    with tempfile.NamedTemporaryFile(mode='r+b') as csv_file:
        writer = csv.writer(csv_file)
        for p in Presentation.objects.filter(replaced_by__isnull=False):
            writer.writerow([p.bnf_code, p.current_version.bnf_code])
        csv_file.seek(0)
        load_data_from_file(
            dataset_name, bq_table_name,
            csv_file.name,
            BNF_MAP_SCHEMA
        )


def write_temp_code_table(level):
    sql = """
    SELECT
      bnf.%s
    FROM
      ebmdatalab.hscic.normalised_prescribing AS prescribing
    RIGHT JOIN
      ebmdatalab.hscic.bnf bnf
    ON
      prescribing.normalised_bnf_code = bnf.presentation_code
    GROUP BY
      bnf.%s
    HAVING
      COUNT(prescribing.bnf_code) = 0
    """ % (level, level)
    client = bigquery.client.Client(project='ebmdatalab')
    dataset = client.dataset('tmp_eu')
    table = dataset.table(
        name="unused_codes_%s" % level)
    job = client.run_async_query("create_%s_%s" % (
        table.name, int(time.time())), sql)
    job.destination = table
    job.use_query_cache = False
    job.use_legacy_sql = False
    job.write_disposition = 'WRITE_TRUNCATE'
    job.allow_large_results = True
    logger.info("Scanning %s to see if it has zero prescribing" % level)
    wait_for_job(job)
    return table


def cleanup_empty_classes():
    classes = [
        ('section_code',
         Section,
         'bnf_id'),
        ('para_code',
         Section,
         'bnf_id'),
        ('chemical_code',
         Chemical,
         'bnf_code'),
        ('product_code',
         Product,
         'bnf_code'),
    ]
    for class_column, model, bnf_field in classes:
        temp_table = write_temp_code_table(class_column)
        converted_uri = "gs://ebmdatalab/tmp/%s.csv.gz" % temp_table.name
        logger.info("Copying %s to %s", (temp_table.name, converted_uri))
        copy_table_to_gcs(temp_table, converted_uri)
        local_path = "/%s/%s.csv" % (tempfile.gettempdir(), temp_table.name)
        logger.info("Downloading %s to %s" % (converted_uri, local_path))
        csv_path = download_from_gcs(converted_uri, local_path)
        logger.info("Marking all classes in %s as not current" % local_path)
        with transaction.atomic():
            with open(csv_path, 'r') as f:
                reader = csv.reader(f)
                next(reader, None)  # skip header
                for row in reader:
                    code = row[0]
                    kwargs = {bnf_field: code}
                    try:
                        obj = model.objects.get(**kwargs)
                        obj.is_current = False
                        obj.save()
                    except model.DoesNotExist:
                        #  Reasons this might happen without cause for alarm:
                        #
                        #  * We don't create paragraphs ending in
                        #    zero, as these data properly belong with
                        #   their section;
                        #
                        #  * We don't currently import appliances and similar
                        logger.warn("Couldn't find %s(pk=%s)", (
                            model.__name__, code))


def update_existing_prescribing():
    update_sql = """
        UPDATE %s
        SET presentation_code = '%s'
        WHERE presentation_code = '%s'"""
    tables_sql = """
        SELECT
          c.relname AS child
        FROM
          pg_inherits
        JOIN pg_class AS c
          ON (inhrelid=c.oid)
        JOIN pg_class AS p
          ON (inhparent=p.oid)
         WHERE p.relname = 'frontend_prescription'"""

    with connection.cursor() as cursor:
        cursor.execute(tables_sql)
        for row in cursor.fetchall():
            table_name = row[0]
            with transaction.atomic():
                for p in Presentation.objects.filter(
                        replaced_by__isnull=False):
                    cursor.execute(
                        update_sql % (
                            table_name,
                            p.current_version.bnf_code,
                            p.bnf_code)
                    )
    print "Now delete `update_existing_prescribing` migration"


def create_bigquery_view():
    sql = """
    SELECT
      prescribing.*,
      COALESCE(bnf_map.current_bnf_code, prescribing.bnf_code)
        AS normalised_bnf_code
    FROM
      ebmdatalab.hscic.prescribing AS prescribing
    LEFT JOIN
      ebmdatalab.hscic.bnf_map AS bnf_map
    ON
      bnf_map.former_bnf_code = prescribing.bnf_code

    """
    client = bigquery.client.Client(project='ebmdatalab')
    # delete the table if it exists
    dataset = Dataset("hscic", client)
    table = dataset.table('normalised_prescribing')
    table.view_query = sql
    try:
        table.create()
    except Conflict:
        pass


class Command(BaseCommand):
    args = ''
    help = 'Imports presentation replacements.'

    def add_arguments(self, parser):
        parser.add_argument(
            'filenames',
            nargs='*',
            help='This argument only exists for tests. Normally the command '
            'is expected to work on the contents of `presentation_commands/`'
        )

    def handle(self, *args, **options):
        if options['filenames']:
            filenames = reversed(sorted(options['filenames']))
        else:
            filenames = reversed(
                sorted(glob.glob(
                    'frontend/management/commands/'
                    'presentation_replacements/*.txt')
                )
            )
        create_code_mapping(filenames)
        create_bigquery_table()
        create_bigquery_view()
        update_existing_prescribing()
        cleanup_empty_classes()
