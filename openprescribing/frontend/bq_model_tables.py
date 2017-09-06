from django.conf import settings

from ebmdatalab.bq_client import BQModelTable
from frontend import models as frontend_models


class BQ_CCGs(BQModelTable):
    # This uses CCG_SCHEMA
    table_name = 'ccgs'
    model = frontend_models.PCT
    fields = [
        ('code', 'STRING'),
        ('name', 'STRING'),
        ('ons_code', 'STRING'),
        ('org_type', 'STRING'),
        ('open_date', 'TIMESTAMP'),
        ('close_date', 'TIMESTAMP'),
        ('address', 'STRING'),
        ('postcode', 'STRING'),
    ]

    @staticmethod
    def pg_to_bq_transform(row):
        if row[4]:
            row[4] = "%s 00:00:00" % row[4]
        if row[5]:
            row[5] = "%s 00:00:00" % row[5]
        return row


class BQ_Prescribing(BQModelTable):
    # This uses PRESCRIBING_SCHEMA
    model = frontend_models.Prescription
    fields = [
        ('sha', 'STRING'),
        ('pct', 'STRING'),
        ('practice', 'STRING'),
        ('bnf_code', 'STRING'),
        ('bnf_name', 'STRING'),
        ('items', 'INTEGER'),
        ('net_cost', 'FLOAT'),
        ('actual_cost', 'FLOAT'),
        ('quantity', 'INTEGER'),
        ('month', 'TIMESTAMP'),
    ]


class BQ_Prescribing_Legacy(BQ_Prescribing):
    table_name = 'normalised_prescribing_legacy'


class BQ_Prescribing_Standard(BQ_Prescribing):
    table_name = 'normalised_prescribing_standard'


class BQ_Presentation(BQModelTable):
    # This uses PRESENTATION_SCHEMA
    table_name = 'presentation'
    model = frontend_models.Presentation
    fields = [
        ('bnf_code', 'STRING'),
        ('name', 'STRING'),
        ('is_generic', 'BOOLEAN'),
        ('active_quantity', 'FLOAT'),
        ('adq', 'FLOAT'),
        ('adq_unit', 'STRING'),
        ('percent_of_adq', 'FLOAT'),
    ]

    @staticmethod
    def pg_to_bq_transform(row):
        if row[2] == 't':
            row[2] = 'true'
        else:
            row[2] = 'false'
        return row


class BQ_Practices(BQModelTable):
    # This uses PRACTICE_SCHEMA
    table_name = settings.BQ_PRACTICES_TABLE_NAME  # practices or test_practices
    model = frontend_models.Practice
    fields = [
        ('code', 'STRING'),
        ('name', 'STRING'),
        ('address1', 'STRING'),
        ('address2', 'STRING'),
        ('address3', 'STRING'),
        ('address4', 'STRING'),
        ('address5', 'STRING'),
        ('postcode', 'STRING'),
        ('location', 'STRING'),
        ('ccg_id', 'STRING'),
        ('setting', 'INTEGER'),
        ('close_date', 'STRING'),
        ('join_provider_date', 'STRING'),
        ('leave_provider_date', 'STRING'),
        ('open_date', 'STRING'),
        ('status_code', 'STRING'),
    ]


class BQ_PracticeStatistics(BQModelTable):
    # This uses PRACTICE_STATISTICS_SCHEMA
    table_name = 'practice_statistics'
    model = frontend_models.PracticeStatistics
    fields = [
        ('month', 'TIMESTAMP'),
        ('male_0_4', 'INTEGER'),
        ('female_0_4', 'INTEGER'),
        ('male_5_14', 'INTEGER'),
        ('male_15_24', 'INTEGER'),
        ('male_25_34', 'INTEGER'),
        ('male_35_44', 'INTEGER'),
        ('male_45_54', 'INTEGER'),
        ('male_55_64', 'INTEGER'),
        ('male_65_74', 'INTEGER'),
        ('male_75_plus', 'INTEGER'),
        ('female_5_14', 'INTEGER'),
        ('female_15_24', 'INTEGER'),
        ('female_25_34', 'INTEGER'),
        ('female_35_44', 'INTEGER'),
        ('female_45_54', 'INTEGER'),
        ('female_55_64', 'INTEGER'),
        ('female_65_74', 'INTEGER'),
        ('female_75_plus', 'INTEGER'),
        ('total_list_size', 'INTEGER'),
        ('astro_pu_cost', 'FLOAT'),
        ('astro_pu_items', 'FLOAT'),
        ('star_pu', 'STRING'),
        ('pct_id', 'STRING'),
        ('practice', 'STRING'),
    ]

    @property
    def pg_columns(self):
        columns = super(BQ_PracticeStatistics, self).pg_columns
        columns[0] = 'date'
        columns[-1] = 'practice_id'
        return columns

    @staticmethod
    def pg_to_bq_transform(row):
        row[0] = "%s 00:00:00" % row[0]  # BQ TIMESTAMP format
        return row
