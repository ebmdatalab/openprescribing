"""This command deals with the fact that the NHS mutates its
prescribing identifiers periodically, making tracking changes through
time very difficult.

As of 2017 (but this is expected to change within the next year), NHS
England uses a derivative of the BNF (British National Formulary)
codes to identify each presentation dispensed, called the NHS Pseudo
Classification.

Unfortunately, both the BNF and the NHS make changes to codes
periodically. Sometimes a chemical gets a new code, or sometimes it
moves to a new section. Because the BNF code includes the section in
the first few characters of the code, just reclassifying a drug means
its unique identifier has changed.  This makes tracking that drug
through time impossible.

The situation is further complicated that the BNF no longer maintains
its old classification, so the Pseudo codes now used by the NHS no
longer necessarily correspond with official BNF codes at all.

The situation is expected to improve with the introduction of ePACT2
and the moving of prescribing data to use SNOMED codes as per dm+d.

For the being, this method aims to normalise all codes in our dataset
so that prescribing is always indexed by the most recent version of
the Pseudo BNF Code.

We achieve this by applying a mapping of old code to new code which
has been applied annualy by NHSBSA to create their Pseduo code list.
This mapping has been supplied to us in private correspondence with
the NHS BSA, and is reproduced (with some corrections to obvious
typos, etc) in the files accompanying this module.

The normalisation process is as follows:

For each old code -> new code mapping, in reverse order of date
(i.e. starting with the most recent mappings):

* If the code is at the section, paragraph, chemical or product level,
  mark our internal corresponding model for that classification as no
  longer current

* Find every presentation matching the new code (or classification),
  and ensure a presentation exists matching the old code.  Create a
  reference to the new presentation code from the old one.

* Create a table of mappings from old codes to the most recent current
  code (taking into account multlple code changes)

* Create a View in bigquery that joins with this table to produce a
  version of the prescribing data with only the most current BNF
  codes; this is used to generate our local version of the prescribing
  data, our measures, and so on, henceforward.

* Replace all the codes that have new normalised versions in all local
  version of the prescribing data.  (If this command ever needs
  running again, some time could be saved by applying this only to
  prescribing data downloaded since the last this command was run)

* Iterate over all known BNF codes, sections, paragraphs etc, looking
  for codes which have never been prescribed, and mark these as not
  current.  This is necessary because sometimes our mappings involve a
  chemical-level change without making this explicit (i.e. a 15
  character BNF code mapping has been supplied, but in fact it's the
  Chemical part of the code that has changed).  In these cases, we
  can't tell if the Chemical is now redundant without checking to see
  if there is any other prescribing under that code.  This process
  also has the useful side effect of removing the (many thousands of)
  codes that have never actually been prescribed, and are therefore
  unhelpful noise in our user interface.

  * The problem with this approach is that recently added codes may
    not yet have prescribing, but may do so at some point in the
    future. Therefore, there is a `refresh_class_currency` method that
    is always called as part of the `import_hscic_prescribing`
    management command, which iterates over all sections, paragraphs,
    chemicals and products currently listed as not current, and checks
    to see if there has been any prescribing this month.

This command should in theory only have to be run once a year, as
we've been told mappings only happen this frequently.  And in theory,
2017 is the last year of using BNF codes.

"""

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
                if not re.match(r'^[0-9A-Z]+$', next_code):
                    # Skip 'withdrawn' &c
                    continue

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
                matches = Presentation.objects.filter(
                    bnf_code__startswith=next_code)
                for row in matches:
                    replaced_by_id = row.pk
                    old_bnf_code = prev_code + replaced_by_id[len(prev_code):]
                    try:
                        old_version = Presentation.objects.get(pk=old_bnf_code)
                    except Presentation.DoesNotExist:
                        old_version = row
                        old_version.pk = None  # allows us to clone
                        old_version.bnf_code = old_bnf_code
                    old_version.replaced_by_id = replaced_by_id
                    old_version.save()


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
        ('presentation_code',
         Presentation,
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
                        logger.warn("Couldn't find %s(pk=%s)" % (
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


def create_bigquery_views():
    # We have to create legacy and standard versions of the view, as a
    # legacy query cannot address a standard view, and vice versa, and
    # we use both flavours in our code.
    sql = """
    SELECT
      prescribing.sha AS sha,
      prescribing.pct AS pct,
      prescribing.practice AS practice,
      COALESCE(bnf_map.current_bnf_code, prescribing.bnf_code)
        AS bnf_code,
      prescribing.bnf_name AS bnf_name,
      prescribing.items AS items,
      prescribing.net_cost AS net_cost,
      prescribing.actual_cost AS actual_cost,
      prescribing.quantity AS quantity,
      prescribing.month AS month,
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
    table = dataset.table('normalised_prescribing_standard')
    table.view_query = sql
    table.view_use_legacy_sql = False
    try:
        table.create()
    except Conflict:
        pass
    table = dataset.table('normalised_prescribing_legacy')
    sql = sql.replace(
        'ebmdatalab.hscic.prescribing',
        '[ebmdatalab:hscic.prescribing]')
    sql = sql.replace(
        'ebmdatalab.hscic.bnf_map',
        '[ebmdatalab:hscic.bnf_map]',
        )
    table.view_query = sql
    table.view_use_legacy_sql = True
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
        create_bigquery_views()
        update_existing_prescribing()
        cleanup_empty_classes()
