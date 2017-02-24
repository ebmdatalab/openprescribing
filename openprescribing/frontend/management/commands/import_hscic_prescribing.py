import csv
import datetime
import glob
import logging
import re

from django.core.management.base import BaseCommand
from django.db import connection

from frontend.models import PCT, ImportLog

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    args = ''
    help = 'Import all data from any data files that have been downloaded. '
    help += 'Set DEBUG to False in your settings before running this.'

    def add_arguments(self, parser):
        parser.add_argument('--filename')
        parser.add_argument('--migrate', action='store_true')
        parser.add_argument(
            '--date', help="Specify date rather than infer it from filename")
        parser.add_argument(
            '--skip-orgs',
            action='store_true',
            help="Don't parse orgs from the file")
        parser.add_argument('--truncate')

    def get_all_dates(self):
        sql = """
        SELECT
          CONCAT(LEFT(split_part(table_name,
                '_',
                3), 4), '-', RIGHT(split_part(table_name,
                '_',
                3), 2), '-01')
        FROM
          information_schema.tables
        WHERE
          table_schema = 'public'
          AND table_name LIKE 'frontend_prescription_%'
        ORDER BY
          table_name;
        """
        with connection.cursor() as cursor:
            cursor.execute(sql)
            return [datetime.datetime.strptime(
                x[0], '%Y-%m-%d').date() for x in cursor.fetchall()]

    def handle(self, *args, **options):
        if options['truncate']:
            self.truncate = True
        else:
            self.truncate = False
        if options['migrate']:
            if options['date']:
                date = datetime.datetime.strptime(
                    options['date'], '%Y-%m-%d').date()
                dates = [date]
            else:
                dates = self.get_all_dates()
            self.drop_redundant_columns()
            for date in dates:
                print "migrating", date
                self.drop_redundant_indexes(date)
                self.create_new_indexes(date)
        else:
            if options['filename']:
                files_to_import = [options['filename']]
            else:
                filepath = './data/raw_data/T*PDPI+BNFT_formatted*'
                files_to_import = glob.glob(filepath)
            for f in files_to_import:
                if options['date']:
                    date = datetime.datetime.strptime(
                        options['date'], '%Y-%m-%d').date()
                else:
                    date = self._date_from_filename(f)
                if not options['skip_orgs']:
                    self.import_pcts(f, date)
                self.drop_partition(date)
                self.create_partition(date)
                self.import_prescriptions(f, date)
                self.create_partition_indexes(date)
                self.add_parent_trigger()
                self.drop_oldest_month(date)

    def import_pcts(self, filename, date):
        logger.info('Importing PCTs from %s' % filename)
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

    def create_partition(self, date):
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
            self._partition_name(date),
            constraint_from,
            constraint_to
        )
        with connection.cursor() as cursor:
            cursor.execute(sql)
        logger.info("Created partition %s" % self._partition_name(date))

    def drop_oldest_month(self, date):
        five_years_ago = datetime.date(date.year - 5, date.month, date.day)
        self.drop_partition(five_years_ago)

    def _partition_name(self, date):
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

    def drop_redundant_columns(self):
        with connection.cursor() as cursor:
            cursor.execute(
                "ALTER TABLE frontend_prescription "
                "DROP COLUMN sha_id CASCADE")
            cursor.execute(
                "ALTER TABLE frontend_prescription "
                "DROP COLUMN chemical_id CASCADE")
            cursor.execute(
                "ALTER TABLE frontend_prescription "
                "DROP COLUMN presentation_name CASCADE")

    def drop_redundant_indexes(self, date):
        indexes = [
            "DROP INDEX %s_by_pct",
            "DROP INDEX %s_by_prac_date_code ",
            "DROP INDEX %s_by_practice",
            "DROP INDEX %s_idx_date_and_code",
            "DROP INDEX %s_by_pct_and_presentation",
            "DROP INDEX %s_by_practice_and_code"
        ]
        partition_name = self._partition_name(date)
        with connection.cursor() as cursor:
            for index_sql in indexes:
                cursor.execute(index_sql % (
                    partition_name))

    def create_new_indexes(self, date):
        indexes = [
            ("CREATE INDEX idx_%s_presentation "
             "ON %s (presentation_code varchar_pattern_ops)"),
            ("CREATE INDEX idx_%s_pct_id "
             "ON %s (pct_id)"),
            ("CREATE INDEX idx_%s_date "
             "ON %s (processing_date)"),
            ("CLUSTER %s USING idx_%s_presentation"),
        ]
        partition_name = self._partition_name(date)
        with connection.cursor() as cursor:
            for index_sql in indexes:
                cursor.execute(index_sql % (
                    partition_name, partition_name))

    def create_partition_indexes(self, date):
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
        partition_name = self._partition_name(date)
        with connection.cursor() as cursor:
            for index_sql in indexes:
                cursor.execute(index_sql % (
                    partition_name, partition_name))
            for constraint_sql in constraints:
                cursor.execute(constraint_sql % (
                    partition_name, partition_name))

    def drop_partition(self, date):
        logger.info('Dropping partition %s' % self._partition_name(date))
        sql = "DROP TABLE IF EXISTS %s" % self._partition_name(date)
        with connection.cursor() as cursor:
            cursor.execute(sql)

    def import_prescriptions(self, filename, date):
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
            cursor.copy_expert(copy_str % self._partition_name(date), file_obj)
            ImportLog.objects.create(
                current_at=date,
                filename=filename,
                category='prescribing'
            )

    def _date_from_filename(self, filename):
        file_str = filename.split('/')[-1].split('.')[0]
        file_str = re.sub(r'PDPI.BNFT_formatted', '', file_str)
        return datetime.date(int(file_str[1:5]), int(file_str[5:]), 1)
