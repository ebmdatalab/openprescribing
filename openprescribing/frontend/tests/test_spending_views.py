from __future__ import division

import collections
import itertools
import random

from django.test import TestCase
from django.db import connection
from django.db.models import Max

from dateutil.relativedelta import relativedelta
from dateutil.parser import parse as parse_date

from frontend.models import (
    Practice, PCT, Prescription, Presentation
)
from dmd.models import (
    DMDProduct, DMDVmpp, NCSOConcession, TariffPrice, TariffCategory
)

from frontend.views.views import (
    NATIONAL_AVERAGE_DISCOUNT_PERCENTAGE, _ncso_spending_for_entity,
    _ncso_spending_breakdown_for_entity
)


class TestSpendingViews(TestCase):

    @classmethod
    def setUpClass(cls):
        super(TestSpendingViews, cls).setUpClass()
        factory = DataFactory()
        cls.months = factory.create_months('2018-02-01', 6)
        # Our NCSO and tariff data extends further than our prescribing data by
        # a couple of months
        cls.prescribing_months = cls.months[:-2]
        # Create some CCGs (we need more than one so we can test aggregation
        # across CCGs at the All England level)
        cls.ccgs = [factory.create_ccg() for _ in range(2)]
        # Populate those CCGs with practices
        cls.practices = []
        for ccg in cls.ccgs:
            for _ in range(2):
                cls.practices.append(factory.create_practice(ccg=ccg))
        # Create some presentations
        cls.presentations = factory.create_presentations(6)
        # Create drug tariff and price concessions costs for these presentations
        factory.create_tariff_and_ncso_costings(cls.presentations, cls.months)
        # Create prescribing for each of the practices we've created
        for practice in cls.practices:
            factory.create_prescribing(
                practice, cls.presentations, cls.prescribing_months
            )
        # Create and populate the materialized view table we need
        factory.populate_presentation_summary_by_ccg_view()
        # Pull out an individual practice and CCG to use in our tests
        cls.practice = cls.practices[0]
        cls.ccg = cls.ccgs[0]

    def test_ncso_spending_methods(self):
        entities = [
            (self.practice, 'practice'),
            (self.ccg, 'CCG'),
            (None, 'all_england'),
        ]
        for entity, entity_type in entities:
            # When we switch to Python 3 we should use the subTest method to
            # make test failures clearer:
            # https://docs.python.org/3/library/unittest.html#subtests
            # with self.subTest(entity=entity, entity_type=entity_type):
            self.validate_ncso_spending_for_entity(
                entity, entity_type, len(self.months)
            )
            self.validate_ncso_spending_breakdown_for_entity(
                entity, entity_type, self.months[0]
            )
            self.validate_ncso_spending_breakdown_for_entity(
                entity, entity_type, self.months[-1]
            )

    def validate_ncso_spending_for_entity(self, *args, **kwargs):
        # with self.subTest(function='_ncso_spending_for_entity'):
        results = _ncso_spending_for_entity(*args, **kwargs)
        expected = recalculate_ncso_spending_for_entity(*args, **kwargs)
        self.assertEqual(results, expected)

    def validate_ncso_spending_breakdown_for_entity(self, *args, **kwargs):
        # with self.subTest(function='_ncso_spending_breakdown_for_entity'):
        results = _ncso_spending_breakdown_for_entity(*args, **kwargs)
        expected = recalculate_ncso_spending_breakdown_for_entity(*args, **kwargs)
        self.assertEqual(results, expected)

    def test_spending_views(self):
        # Basic smoketest which just checks that the view loads OK and has
        # something we expect in it
        urls = [
            '/practice/{}/concessions/'.format(self.practice.code),
            '/ccg/{}/concessions/'.format(self.ccg.code),
            '/all-england/concessions/'
        ]
        for url in urls:
            # with self.subTest(url=url):
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)
            ctx = response.context
            self.assertEqual(
                ctx['breakdown_date'].strftime('%Y-%m-%d'),
                self.months[-1]
            )


class DataFactory(object):
    """
    This class provides methods to generate test fixtures programatically
    """

    def __init__(self, seed=1):
        self.random = random.Random()
        self.random.seed(seed)
        counter = itertools.count()
        self.next_id = lambda: next(counter)

    def create_months(self, start_date, num_months):
        date = parse_date(start_date)
        return [
            (date + relativedelta(months=i)).strftime('%Y-%m-%d')
            for i in range(0, num_months)
        ]

    def create_practice(self, ccg=None):
        if ccg is None:
            ccg = self.create_ccg()
        index = self.next_id()
        return Practice.objects.create(
            name='Practice {}'.format(index),
            code='ABC{:03}'.format(index),
            ccg=ccg
        )

    def create_ccg(self):
        index = self.next_id()
        return PCT.objects.create(
            name='CCG {}'.format(index),
            code='A{:02}'.format(index),
            org_type='CCG'
        )

    def create_presentations(self, num_presentations):
        presentations = []
        for i in range(num_presentations):
            presentation = Presentation.objects.create(
                bnf_code='0123456789ABCD{}'.format(i),
                name='Foo Tablet {}'.format(i)
            )
            product = DMDProduct.objects.create(
                bnf_code=presentation.bnf_code,
                dmdid=i,
                vpid=i,
                name='DMD '+presentation.name
            )
            DMDVmpp.objects.create(
                vppid=i*10,
                vpid=product.vpid,
                nm='VMPP '+presentation.name,
                qtyval=2
            )
            presentations.append(presentation)
        return presentations

    def create_tariff_and_ncso_costings(self, presentations, months):
        tariff_category = TariffCategory.objects.create(cd=1, desc='')
        for presentation in presentations:
            product = DMDProduct.objects.get(bnf_code=presentation.bnf_code)
            vmpp = DMDVmpp.objects.get(vpid=product.vpid)
            for date in months:
                tariff_price = TariffPrice.objects.create(
                    date=date,
                    vmpp=vmpp,
                    product=product,
                    tariff_category=tariff_category,
                    price_pence=self.random.randint(10, 100)
                )
                if self.random.choice([True, False]):
                    NCSOConcession.objects.create(
                        vmpp=vmpp,
                        date=date,
                        drug='',
                        pack_size='',
                        price_concession_pence=(
                            tariff_price.price_pence + self.random.randint(10, 100)
                        )
                    )

    def create_prescribing(self, practice, presentations, months):
        for date in months:
            for i, presentation in enumerate(presentations):
                Prescription.objects.create(
                    processing_date=date,
                    practice=practice,
                    pct_id=practice.ccg_id,
                    presentation_code=presentation.bnf_code,
                    quantity=i+1,
                    total_items=0,
                    actual_cost=0,
                )

    def populate_presentation_summary_by_ccg_view(self):
        with connection.cursor() as cursor:
            with open('frontend/management/commands/replace_matviews.sql', 'r') as f:
                cursor.execute(f.read())
            cursor.execute("""
                INSERT INTO
                  vw__presentation_summary_by_ccg
                  (
                    processing_date,
                    pct_id,
                    presentation_code,
                    items,
                    cost,
                    quantity
                  )
                (
                  SELECT
                    processing_date,
                    pct_id,
                    presentation_code,
                    SUM(total_items),
                    SUM(actual_cost),
                    SUM(quantity)
                  FROM
                    frontend_prescription
                  GROUP BY
                    processing_date,
                    pct_id,
                    presentation_code
                )
            """)


##############################################################################
# Below are functions which reimplement the NCSO spending calculations using
# (as far as possible) Python rather than SQL so we have something to test the
# SQL against
##############################################################################


def recalculate_ncso_spending_for_entity(entity, entity_type, num_months):
    prescriptions = get_prescriptions_for_entity(entity, entity_type)
    last_prescribing_date = get_last_prescribing_date()
    quantities = aggregate_quantities_by_date_and_bnf_code(prescriptions)
    concessions = get_ncso_concessions(*get_start_and_end_dates(num_months))
    concessions = add_quantities_to_concessions(
        concessions, quantities, last_prescribing_date
    )
    concessions = filter_zero_prescribing_quantities(concessions)
    concessions = calculate_costs_for_concessions(concessions)
    results = []
    for row in aggregate_by_date(concessions):
        results.append({
            'month': row['date'],
            'tariff_cost': round(row['tariff_cost'], 5),
            'additional_cost': round(row['additional_cost'], 5),
            'is_estimate': row['is_estimate'],
            'last_prescribing_date': last_prescribing_date
        })
    results.sort(key=lambda row: row['month'])
    return results


def recalculate_ncso_spending_breakdown_for_entity(entity, entity_type, month):
    prescriptions = get_prescriptions_for_entity(entity, entity_type)
    last_prescribing_date = get_last_prescribing_date()
    quantities = aggregate_quantities_by_date_and_bnf_code(prescriptions)
    concessions = get_ncso_concessions(month, month)
    concessions = add_quantities_to_concessions(
        concessions, quantities, last_prescribing_date
    )
    concessions = filter_zero_prescribing_quantities(concessions)
    concessions = calculate_costs_for_concessions(concessions)
    results = []
    for row in concessions:
        results.append((
            row['bnf_code'],
            row['product_name'],
            row['quantity'],
            round(row['tariff_cost'], 5),
            round(row['additional_cost'], 5)
        ))
    results.sort(
        key=lambda row: (row[4], row[3]),
        reverse=True
    )
    return results


def get_prescriptions_for_entity(entity, entity_type):
    query = Prescription.objects.all()
    if entity_type == 'practice':
        return query.filter(practice=entity)
    elif entity_type == 'CCG':
        return query.filter(pct=entity)
    elif entity_type == 'all_england':
        return query
    else:
        raise ValueError('Unknown entity_type: {}'.format(entity_type))


def get_start_and_end_dates(num_months):
    end_date = NCSOConcession.objects.aggregate(Max('date'))['date__max']
    start_date = end_date - relativedelta(months=(num_months-1))
    return start_date, end_date


def get_ncso_concessions(start_date, end_date):
    concessions = []
    query = NCSOConcession.objects.filter(
        date__gte=start_date, date__lte=end_date
    )
    for ncso in query:
        tariff = TariffPrice.objects.get(vmpp=ncso.vmpp, date=ncso.date)
        product = tariff.product
        concessions.append({
            'date': ncso.date,
            'bnf_code': product.bnf_code,
            'product_name': product.name,
            'tariff_price_pence': tariff.price_pence,
            'concession_price_pence': ncso.price_concession_pence,
            'quantity_value': ncso.vmpp.qtyval
        })
    return concessions


def aggregate_quantities_by_date_and_bnf_code(prescriptions):
    quantities = collections.defaultdict(float)
    for prescription in prescriptions:
        key = (prescription.processing_date, prescription.presentation_code)
        quantities[key] += prescription.quantity
    return quantities


def get_last_prescribing_date():
    result = Prescription.objects.aggregate(Max('processing_date'))
    return result['processing_date__max']


def add_quantities_to_concessions(concessions, quantities, last_prescribing_date):
    for concession in concessions:
        source_date = concession['date']
        is_estimate = False
        if source_date > last_prescribing_date:
            source_date = last_prescribing_date
            is_estimate = True
        key = (source_date, concession['bnf_code'])
        concession['quantity'] = quantities[key]
        concession['is_estimate'] = is_estimate
    return concessions


def filter_zero_prescribing_quantities(concessions):
    return [i for i in concessions if i['quantity'] != 0]


def calculate_costs_for_concessions(concessions):
    for concession in concessions:
        concession.update(calculate_concession_costs(concession))
    return concessions


def calculate_concession_costs(concession):
    num_units = concession['quantity'] / concession['quantity_value']
    tariff_cost_pence = num_units * concession['tariff_price_pence']
    concession_cost_pence = num_units * concession['concession_price_pence']
    tariff_cost = tariff_cost_pence / 100
    concession_cost = concession_cost_pence / 100
    tariff_cost_discounted = tariff_cost * (
        1 - (NATIONAL_AVERAGE_DISCOUNT_PERCENTAGE / 100)
    )
    concession_cost_discounted = concession_cost * (
        1 - (NATIONAL_AVERAGE_DISCOUNT_PERCENTAGE / 100)
    )
    return {
        'tariff_cost': tariff_cost_discounted,
        'additional_cost': concession_cost_discounted - tariff_cost_discounted
    }


def aggregate_by_date(concessions):
    by_date = {}
    for concession in concessions:
        if concession['date'] not in by_date:
            aggregate = {
                'date': concession['date'],
                'is_estimate': concession['is_estimate'],
                'quantity': 0,
                'tariff_cost': 0,
                'additional_cost': 0
            }
            by_date[concession['date']] = aggregate
        else:
            aggregate = by_date[concession['date']]
        aggregate['quantity'] += concession['quantity']
        aggregate['tariff_cost'] += concession['tariff_cost']
        aggregate['additional_cost'] += concession['additional_cost']
    return by_date.values()
