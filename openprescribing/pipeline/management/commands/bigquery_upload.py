from __future__ import print_function

from django.core.management import BaseCommand
from django.db.models import Max

from ebmdatalab import bigquery_old as bigquery
from frontend.models import PracticeStatistics, Prescription

from ...cloud_utils import CloudHandler


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        # Make sure that PracticeStatistics and Prescription tables both have
        # latest data.
        latest_practice_statistic_date = PracticeStatistics.objects\
            .aggregate(Max('date'))['date__max']
        latest_prescription_date = Prescription.objects\
            .aggregate(Max('processing_date'))['processing_date__max']

        if latest_practice_statistic_date != latest_prescription_date:
            msg = 'Latest PracticeStatistics object has date {}, '\
                'while latest Prescription object has processing_date {}'\
                .format(latest_practice_statistic_date, latest_prescription_date)
            raise CommandError(msg)

        BigQueryUploader().update_bnf_table()
        bigquery.load_data_from_pg(
            'hscic', 'practices', 'frontend_practice',
            bigquery.PRACTICE_SCHEMA)
        bigquery.load_presentation_from_pg()
        bigquery.load_statistics_from_pg()
        bigquery.load_ccgs_from_pg()


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
