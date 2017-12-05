import csv
import datetime
import logging
import re
import tempfile

from dateutil.relativedelta import relativedelta

from django.core.management.base import BaseCommand
from django.db import connection
from django.db import transaction

from frontend.models import Chemical
from frontend.models import ImportLog
from frontend.models import PCT
from frontend.models import Practice
from frontend.models import PracticeStatistics
from frontend.models import Prescription
from frontend.models import Presentation
from frontend.models import Product
from frontend.models import Section

from gcutils.bigquery import Client, TableExporter


logger = logging.getLogger(__name__)


class Command(BaseCommand):
    args = ''
    help = 'Import all data from any data files that have been downloaded. '
    help += 'Set DEBUG to False in your settings before running this.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--filename',
            help=(
                'A path to a properly converted file on the filesystem'
            ))
        parser.add_argument(
            '--date', help="Specify date rather than infer it from filename")
        parser.add_argument(
            '--skip-orgs',
            action='store_true',
            help="Don't parse orgs from the file")
        parser.add_argument(
            '--reimport-all',
            action='store_true',
            help='Download all data from bigquery and make new set of tables'
        )

    def handle(self, *args, **options):
        if options['reimport_all']:
            self.reimport_all()
        else:
            fname = options['filename']
            if options['date']:
                self.date = datetime.datetime.strptime(
                    options['date'], '%Y-%m-%d').date()
            else:
                self.date = self._date_from_filename(fname)
            if not options['skip_orgs']:
                self.import_pcts_and_practices(fname)
            self.drop_partition()
            self.create_partition()
            self.import_prescriptions(fname)
            self.create_partition_indexes()
            self.add_parent_trigger()
            self.drop_oldest_month()
            self.refresh_class_currency()
        logger.info("Done!")

    def reimport_all(self):
        last_imported = ImportLog.objects.latest_in_category(
            'prescribing').current_at
        self.date = last_imported - relativedelta(years=5)
        client = Client('tmp_eu')
        while self.date <= last_imported:
            date_str = self.date.strftime('%Y-%m-%d')
            sql = ('SELECT pct AS pct_id, practice AS practice_id, '
                   'bnf_code AS presentation_code, items AS total_items, '
                   'net_cost, actual_cost, quantity, '
                   'FORMAT_TIMESTAMP("%%Y_%%m_%%d", month) AS processing_date '
                   'FROM hscic.normalised_prescribing_standard '
                   "WHERE month = '%s'" % date_str)
            table_name = "prescribing_%s" % date_str.replace('-', '_')
            table = client.get_or_create_table(table_name)
            table.insert_rows_from_query(sql)
            exporter = TableExporter(table, 'tmp/{}-*'.format(table_name))
            exporter.export_to_storage()

            with tempfile.NamedTemporaryFile(mode='wb') as tmpfile:
                logger.info("Importing data for %s" % self.date)
                exporter.download_from_storage_and_unzip(tmpfile)
                with transaction.atomic():
                    self.drop_partition()
                    self.create_partition()
                    self.import_prescriptions(tmpfile.name)
                    self.create_partition_indexes()
                    self.add_parent_trigger()
            self.date += relativedelta(months=1)

    def refresh_class_currency(self):
        # For every section, paragraph, chemical and product which is
        # currently marked as not current, see if there has been any
        # prescribing for it in the current month, and if there has,
        # mark it as current
        logger.info("Updating `is_current` on various classifications...")
        classes = [
            (Section, 'bnf_id'),
            (Chemical, 'bnf_code'),
            (Product, 'bnf_code'),
            (Presentation, 'bnf_code'),
        ]
        with transaction.atomic():
            for model, field_name in classes:
                for obj in model.objects.filter(is_current=False):
                    kwargs = {
                        'processing_date': self.date,
                        'presentation_code__startswith': getattr(
                            obj, field_name)
                    }
                    count = Prescription.objects.filter(**kwargs).count()
                    if count > 0:
                        obj.is_current = True
                        obj.save()

    def import_pcts_and_practices(self, filename):
        logger.info('Importing PCTs and practices from %s' % filename)
        rows = csv.reader(open(filename, 'rU'))
        pct_codes = set()
        practices = set()
        for row in rows:
            pct_codes.add(row[0])
            practices.add(row[1])
        pcts_created = practices_created = 0
        with transaction.atomic():
            for pct_code in pct_codes:
                p, created = PCT.objects.get_or_create(code=pct_code)
                pcts_created += created
            for practice_code in practices:
                p, created = Practice.objects.get_or_create(code=practice_code)
                practices_created += created

        logger.info("%s PCTs created" % pcts_created)
        logger.info("%s Practices created" % practices_created)

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
        PracticeStatistics.objects.filter(date__lte=five_years_ago).delete()

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
        copy_str += "total_items,net_cost,actual_cost,"
        copy_str += "quantity,processing_date) FROM STDIN "
        copy_str += "WITH (FORMAT CSV)"
        file_obj = open(filename)
        with connection.cursor() as cursor:
            cursor.copy_expert(copy_str % self._partition_name(), file_obj)
            ImportLog.objects.create(
                current_at=self.date,
                filename=filename,
                category='prescribing'
            )

    def _date_from_filename(self, filename):
        new_style = re.match(r'.*/([0-9]{4}_[0-9]{2})/', filename)
        if new_style:
            year, month = new_style.groups()[0].split('_')
            date = datetime.date(int(year), int(month), 1)
        else:
            file_str = filename.replace('T', '').split('/')[-1].split('.')[0]
            date = datetime.date(int(file_str[0:4]), int(file_str[4:6]), 1)
        return date
