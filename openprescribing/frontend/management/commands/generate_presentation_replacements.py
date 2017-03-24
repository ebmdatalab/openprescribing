import csv
import glob
import re
import tempfile

from django.core.management.base import BaseCommand
from django.core.management.base import CommandError
from google.cloud.bigquery import SchemaField

from frontend.models import Presentation

from ebmdatalab.bigquery import load_data_from_file


BNF_MAP_SCHEMA = [
    SchemaField('former_bnf_code', 'STRING'),
    SchemaField('current_bnf_code', 'STRING'),
]


def create_code_mapping(filenames):
    for f in filenames:
        for line in open(f, 'r'):
            if not line.strip():
                continue  # skip blank lines
            if "\t" not in line:
                raise CommandError(
                    "Input lines must be tab delimited: %s" % line)
            prev_code, next_code = line.split("\t")
            prev_code = prev_code.strip()
            next_code = next_code.strip()
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


def create_bigquery_view():
    pass  # XXX not implemented


class Command(BaseCommand):
    args = ''
    help = 'Imports presentation replacements.'

    def add_arguments(self, parser):
        parser.add_argument('filenames', nargs='*')

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
