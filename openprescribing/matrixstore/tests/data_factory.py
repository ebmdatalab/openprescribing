import csv
import itertools
import json
import random
import tempfile

from django.conf import settings

from dateutil.relativedelta import relativedelta
from dateutil.parser import parse as parse_date

from frontend import bq_schemas as schemas
from gcutils.bigquery import Client


class DataFactory(object):
    """
    This class provides methods to generate test fixtures and upload them to
    BigQuery
    """

    def __init__(self, seed=36):
        self.random = random.Random()
        self.random.seed(seed)
        counter = itertools.count()
        self.next_id = lambda: next(counter)
        self._reset_caches()

    def _reset_caches(self):
        self._practices = []
        self._practice_statistics = []
        self._presentations = []
        self._prescribing = []
        self._bnf_map = []

    def create_months(self, start_date, num_months):
        date = parse_date(start_date)
        return [
            (date + relativedelta(months=i)).strftime('%Y-%m-%d 00:00:00 UTC')
            for i in range(0, num_months)
        ]

    def create_practice(self):
        practice = {'code': 'ABC{:03}'.format(self.next_id())}
        self._practices.append(practice)
        return practice

    def create_practices(self, num_practices):
        return [
            self.create_practice()
            for i in range(num_practices)
        ]

    def create_statistics_for_one_practice_and_month(self, practice, month):
        data = {
            'month': month,
            'practice': practice['code'],
            # We don't care about the PCT at the moment
            'pct_id': '00A',
            'astro_pu_items': self.random.random() * 1000,
            'astro_pu_cost': self.random.random() * 1000,
            'star_pu': json.dumps({
                # This is just a small selection of available STAR-PU values
                'statins_cost': self.random.random() * 1000,
                'hypnotics_adq': self.random.random() * 1000,
                'laxatives_cost': self.random.random() * 1000,
                'analgesics_cost': self.random.random() * 1000,
                'oral_nsaids_cost': self.random.random() * 1000,
            }),
            # We increment this value below
            'total_list_size': 0
        }
        age_bands = (
            '0_4', '5_14', '15_24', '25_34', '35_44',
            '45_54', '55_64', '65_74', '75_plus'
        )
        for age_band in age_bands:
            for sex in ('male', 'female'):
                value = self.random.randint(0, 1000)
                data['{}_{}'.format(sex, age_band)] = value
                data['total_list_size'] += value
        self._practice_statistics.append(data)
        return data

    def create_practice_statistics(self, practices, months):
        return [
            self.create_statistics_for_one_practice_and_month(practice, month)
            for practice in practices
            for month in months
        ]

    def create_presentation(self):
        index = self.next_id()
        presentation = {
            'bnf_code': self.create_bnf_code(index),
            'name': 'Foo Tablet {}'.format(index),
            'is_generic': self.random.choice([True, False]),
            'adq_per_quantity': self.random.choice(
                [None, self.random.random() * 30]
            )
        }
        self._presentations.append(presentation)
        return presentation

    def create_bnf_code(self, index):
        return '0123456789ABCD{}'.format(index)

    def create_presentations(self, num_presentations):
        return [self.create_presentation() for i in range(num_presentations)]

    def create_prescription(self, presentation, practice, month):
        prescription = {
            'month': month,
            'practice': practice['code'],
            'bnf_code': presentation['bnf_code'],
            'bnf_name': presentation['name'],
            'items': self.random.randint(1, 100),
            'quantity': self.random.randint(1, 100),
            'net_cost': self.random.random() * 100,
            'actual_cost': self.random.random() * 100,
            'sha': None,
            'pct': None,
            'stp': None,
            'regional_team': None
        }
        self._prescribing.append(prescription)
        return prescription

    def create_prescribing(self, presentations, practices, months):
        prescribing = []
        for practice in practices:
            # Make sure each practice prescribes in at least one month, although
            # probably not every month
            n = self.random.randint(1, len(months))
            selected_months = self.random.sample(months, n)
            for month in selected_months:
                # Make sure the practice prescribes at least one presentation,
                # although probably not every one
                n = self.random.randint(1, len(presentations))
                selected_presentations = self.random.sample(presentations, n)
                for presentation in selected_presentations:
                    prescribing.append(
                        self.create_prescription(presentation, practice, month)
                    )
        return prescribing

    def update_bnf_code(self, presentation):
        new_bnf_code = self.create_bnf_code(self.next_id())
        self._bnf_map.append({
            'former_bnf_code': presentation['bnf_code'],
            'current_bnf_code': new_bnf_code
        })
        new_presentation = dict(presentation, bnf_code=new_bnf_code)
        # Update references to the old BNF code, if there are any
        indices = [
            i for i, other_presentation
            in enumerate(self._presentations)
            if other_presentation['bnf_code'] == presentation['bnf_code']
        ]
        if indices:
            for i in indices:
                self._presentations[i] = new_presentation
        else:
            self._presentations.append(new_presentation)
        return new_presentation

    def upload_to_bigquery(self):
        client = Client('hscic')
        assert_is_test_dataset(client)
        create_and_populate_bq_table(
            client,
            'presentation',
            schemas.PRESENTATION_SCHEMA,
            self._presentations
        )
        create_and_populate_bq_table(
            client,
            'prescribing',
            schemas.PRESCRIBING_SCHEMA,
            self._prescribing
        )
        create_and_populate_bq_table(
            client,
            'practice_statistics_all_years',
            schemas.PRACTICE_STATISTICS_SCHEMA,
            self._practice_statistics
        )
        create_and_populate_bq_table(
            client,
            'bnf_map',
            schemas.BNF_MAP_SCHEMA,
            self._bnf_map
        )
        self._reset_caches()


def assert_is_test_dataset(client):
    bq_nonce = getattr(settings, 'BQ_NONCE', None)
    if not bq_nonce or str(bq_nonce) not in client.dataset_id:
        raise RuntimeError('BQ_NONCE must be set')


def create_and_populate_bq_table(client, name, schema, table_data):
    table = client.get_or_create_table(name, schema)
    if not table_data:
        return
    with tempfile.NamedTemporaryFile() as f:
        writer = csv.writer(f)
        for item in table_data:
            writer.writerow(dict_to_row(item, schema))
        f.seek(0)
        table.insert_rows_from_csv(f.name)


def dict_to_row(dictionary, schema):
    row = [dictionary[field.name] for field in schema]
    if len(row) != len(schema):
        extra = set(dictionary) - set([field.name for field in schema])
        raise ValueError(
            'Dictionary has keys which are not in BigQuery schema: {}'
            .format(', '.join(extra))
        )
    return row
