import itertools
import random

from django.db import connection

from dateutil.relativedelta import relativedelta
from dateutil.parser import parse as parse_date

from frontend.models import (
    ImportLog, Practice, PCT, Prescription, Presentation
)
from dmd.models import (
    DMDProduct, DMDVmpp, NCSOConcession, TariffPrice, TariffCategory
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

    def create_months_array(self, start_date=None, num_months=1):
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

    def create_presentations(self, num_presentations, vmpp_per_presentation=1):
        presentations = []
        for i in range(num_presentations):
            presentation = Presentation.objects.create(
                bnf_code='0123456789ABCD{}'.format(i),
                name='Foo Tablet {}'.format(i),
                quantity_means_pack=self.random.choice([True, False, None])
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
                qtyval=self.random.randint(5, 25)
            )
            presentations.append(presentation)
        return presentations

    def create_tariff_and_ncso_costings_for_presentations(
            self, presentations, months=None):
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

    def create_prescribing_for_practice(
            self,
            practice,
            presentations=None,
            months=None):
        for date in months:
            self.create_import_log(date)
            for i, presentation in enumerate(presentations):
                Prescription.objects.create(
                    processing_date=date,
                    practice=practice,
                    pct_id=practice.ccg_id,
                    presentation_code=presentation.bnf_code,
                    quantity=self.random.randint(1, 1000),
                    total_items=0,
                    actual_cost=0,
                )

    def create_import_log(self, date):
        ImportLog.objects.create(
            current_at=date,
            category='prescribing'
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
