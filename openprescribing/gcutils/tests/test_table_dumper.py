import csv
import tempfile

from django.test import TestCase

from gcutils.table_dumper import TableDumper
from frontend.models import PCT


class TableDumperTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        PCT.objects.create(code='ABC', name='CCG 1')
        PCT.objects.create(code='XYZ', name='CCG 2')

    def test_dump_to_file_with_transformer(self):
        def transformer(row):
            return [row[0][::-1], row[1].lower()]

        dumper = TableDumper(PCT, ['code', 'name'], transformer)

        with tempfile.TemporaryFile() as f:
            dumper.dump_to_file(f)
            f.seek(0)
            records = list(csv.reader(f))

        self.assertEqual(records, [['CBA', 'ccg 1'], ['ZYX', 'ccg 2']])

    def test_dump_to_file_without_transformer(self):
        dumper = TableDumper(PCT, ['code', 'name'])

        with tempfile.TemporaryFile() as f:
            dumper.dump_to_file(f)
            f.seek(0)
            records = list(csv.reader(f))

        self.assertEqual(records, [['ABC', 'CCG 1'], ['XYZ', 'CCG 2']])
