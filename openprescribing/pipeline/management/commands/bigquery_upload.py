from __future__ import print_function

from django.core.management import BaseCommand

from ebmdatalab import bigquery

from ...cloud_utils import CloudHandler


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
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
