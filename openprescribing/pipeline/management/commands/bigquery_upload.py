from __future__ import print_function

from datetime import date

from django.core.management import BaseCommand, CommandError
from django.db.models import Max

from gcutils.bigquery import Client as BQClient
from gcutils.storage import Client as StorageClient
from frontend import models
from frontend import bq_schemas as schemas


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        # Make sure that PracticeStatistics and Prescription tables both have
        # latest data.
        latest_practice_statistic_date = models.PracticeStatistics.objects\
            .aggregate(Max('date'))['date__max']
        latest_prescription_date = models.Prescription.objects\
            .aggregate(Max('processing_date'))['processing_date__max']

        if latest_practice_statistic_date != latest_prescription_date:
            msg = 'Latest PracticeStatistics object has date {}, '\
                'while latest Prescription object has processing_date {}'\
                .format(latest_practice_statistic_date, latest_prescription_date)
            raise CommandError(msg)

        update_bnf_table()

        client = BQClient('hscic')

        table = client.get_table('practices')
        columns = [field.name for field in schemas.PRACTICE_SCHEMA]
        table.insert_rows_from_pg(models.Practice, columns)

        table = client.get_table('presentation')
        columns = [field.name for field in schemas.PRESENTATION_SCHEMA]
        table.insert_rows_from_pg(
            models.Presentation,
            columns,
            schemas.presentation_transform
        )

        table = client.get_table('practice_statistics')
        columns = [field.name for field in schemas.PRACTICE_STATISTICS_SCHEMA]
        columns[0] = 'date'
        columns[-1] = 'practice_id'
        table.insert_rows_from_pg(
            models.PracticeStatistics,
            columns,
            schemas.statistics_transform
        )

        sql = 'SELECT MAX(month) FROM {hscic}.practice_statistics_all_years'
        results = client.query(sql)
        if results.rows[0][0] is None:
            last_uploaded_practice_statistics_date = date(1900, 1, 1)
        else:
            last_uploaded_practice_statistics_date = results.rows[0][0].date()

        table = client.get_table('practice_statistics_all_years')
        sql = '''SELECT
                    month,
                    pct_id,
                    practice,
                    male_0_4,
                    female_0_4,
                    male_5_14,
                    female_5_14,
                    male_15_24,
                    female_15_24,
                    male_25_34,
                    female_25_34,
                    male_35_44,
                    female_35_44,
                    male_45_54,
                    female_45_54,
                    male_55_64,
                    female_55_64,
                    male_65_74,
                    female_65_74,
                    male_75_plus,
                    female_75_plus,
                    total_list_size
        FROM {hscic}.practice_statistics
        WHERE month > TIMESTAMP('{date}')'''
        substitutions = {'date': last_uploaded_practice_statistics_date}
        table.insert_rows_from_query(
            sql,
            write_disposition='WRITE_APPEND',
            substitutions=substitutions
        )

        table = client.get_table('ccgs')
        columns = [field.name for field in schemas.CCG_SCHEMA]
        table.insert_rows_from_pg(
            models.PCT,
            columns,
            schemas.ccgs_transform
        )


def update_bnf_table():
    """Update `bnf` table from cloud-stored CSV
    """
    storage_client = StorageClient()
    bucket = storage_client.get_bucket()
    blobs = bucket.list_blobs(prefix='hscic/bnf_codes/')
    blobs = sorted(blobs, key=lambda blob: blob.name, reverse=True)
    blob = blobs[0]

    bq_client = BQClient('hscic')
    table = bq_client.get_table('bnf')
    table.insert_rows_from_storage(blob.name, skip_leading_rows=1)
