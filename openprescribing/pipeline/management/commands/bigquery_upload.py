from __future__ import print_function

from django.core.management import BaseCommand, CommandError
from django.db.models import Max

from gcutils.bigquery import Client
from frontend import models
from frontend import bq_schemas as schemas

from ...cloud_utils import CloudHandler


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

        BigQueryUploader().update_bnf_table()

        client = Client('hscic')

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


class BigQueryUploader(CloudHandler):
    def update_bnf_table(self):
        """Update `bnf` table from cloud-stored CSV
        """
        dataset = self.list_raw_datasets(
            'ebmdatalab', prefix='hscic/bnf_codes',
            name_regex=r'\.csv')[-1]
        uri = "gs://ebmdatalab/%s" % dataset
        print("Loading data from %s..." % uri)
        self.load(uri, table_name="bnf", schema='bnf.json')
