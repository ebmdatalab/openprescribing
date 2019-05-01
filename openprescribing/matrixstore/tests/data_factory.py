from __future__ import division

import itertools
import json
import random

from dateutil.relativedelta import relativedelta
from dateutil.parser import parse as parse_date


class DataFactory(object):
    """
    This class provides methods to generate test fixtures for the MatrixStore
    """

    def __init__(self, seed=36):
        self.random = random.Random()
        self.random.seed(seed)
        counter = itertools.count()
        self.next_id = lambda: next(counter)
        self.practices = []
        self.practice_statistics = []
        self.presentations = []
        self.prescribing = []
        self.bnf_map = []

    def create_months(self, start_date, num_months):
        date = parse_date(start_date)
        return [
            (date + relativedelta(months=i)).strftime('%Y-%m-%d 00:00:00 UTC')
            for i in range(0, num_months)
        ]

    def create_practice(self):
        practice = {'code': 'ABC{:03}'.format(self.next_id())}
        self.practices.append(practice)
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
        self.practice_statistics.append(data)
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
        self.presentations.append(presentation)
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
            # Costs should be in pounds to two decimal places
            'net_cost': self.random.randint(1, 10000) / 100,
            'actual_cost': self.random.randint(1, 10000) / 100,
            'sha': None,
            'pct': None,
            'stp': None,
            'regional_team': None
        }
        self.prescribing.append(prescription)
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
        self.bnf_map.append({
            'former_bnf_code': presentation['bnf_code'],
            'current_bnf_code': new_bnf_code
        })
        new_presentation = dict(presentation, bnf_code=new_bnf_code)
        # Update references to the old BNF code, if there are any
        indices = [
            i for i, other_presentation
            in enumerate(self.presentations)
            if other_presentation['bnf_code'] == presentation['bnf_code']
        ]
        if indices:
            for i in indices:
                self.presentations[i] = new_presentation
        else:
            self.presentations.append(new_presentation)
        return new_presentation
