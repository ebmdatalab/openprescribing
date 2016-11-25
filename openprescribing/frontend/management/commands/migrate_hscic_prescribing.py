import datetime
import calendar
import tempfile

from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    args = ''
    help = 'Import all data from any data files that have been downloaded. '
    help += 'Set DEBUG to False in your settings before running this.'

    def handle(self, *args, **options):
        self.migrate_data()

    def migrate_data(self):
        # rename the main table
        with connection.cursor() as cursor:
            cursor.execute("ALTER TABLE frontend_prescription "
                           "RENAME TO frontend_prescription_old")
            # create a new parent table with the same name
            sql = """
            CREATE TABLE frontend_prescription (
                id integer NOT NULL,
                presentation_code character varying(15) NOT NULL,
                presentation_name character varying(1000) NOT NULL,
                total_items integer NOT NULL,
                actual_cost double precision NOT NULL,
                quantity double precision NOT NULL,
                processing_date date NOT NULL,
                chemical_id character varying(9) NOT NULL,
                pct_id character varying(3) NOT NULL,
                practice_id character varying(6) NOT NULL,
                sha_id character varying(3) NOT NULL
            );
            DROP SEQUENCE IF EXISTS frontend_prescription_parent_id_seq;
            CREATE SEQUENCE frontend_prescription_id_seq
                START WITH 1
                INCREMENT BY 1
                NO MINVALUE
                NO MAXVALUE
                CACHE 1;

            ALTER TABLE ONLY frontend_prescription ALTER COLUMN id
              SET DEFAULT
                nextval('frontend_prescription_parent_id_seq'::regclass);
            """
            cursor.execute(sql)
        # month, by month, dump data to a CSV; then reimport
        start_date = datetime.date(2011, 8, 1)
        end_date = datetime.date(2016, 8, 1)
        for date in self.each_date(start_date, end_date):
            start = datetime.datetime.now()
            print "Copying", date
            query = ("COPY (select * from frontend_prescription) "
                     "TO STDOUT WITH CSV HEADER")
            with tempfile.NamedTemporaryFile(mode='rb+') as f:
                with connection.cursor() as cursor:
                    cursor.copy_expert(query, f)
                    print "  importing", date
                    call_command(
                        'import_hscic_prescribing',
                        filename=f.name,
                        skip_orgs=True,
                        date=date.strftime("%Y-%m-%d"))
            print "  %s seconds elapsed" % (
                datetime.datetime.now() - start).seconds
        print "Done. Now check the data in frontend_prescription."
        print "If you're happy, drop frontend_prescription_old"

    def each_date(self, start_date, end_date):
        date = start_date
        while date <= end_date:
            yield date
            month = date.month
            year = int(date.year + month / 12)
            month = month % 12 + 1
            day = min(date.day, calendar.monthrange(year, month)[1])
            date = datetime.date(year, month, day)
