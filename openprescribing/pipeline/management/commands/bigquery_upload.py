from __future__ import print_function

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
