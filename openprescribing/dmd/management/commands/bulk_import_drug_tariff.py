"""Bulk importer for manually-prepared tariff CSV.


This probably won't be used again following initial data load, so
could be deleted after that.

"""
import csv
import logging
from datetime import datetime

from django.core.management.base import BaseCommand
from django.db import transaction

from dmd.models import TariffPrice
from dmd.models import DMDVmpp
from dmd.models import DMDProduct
from frontend.models import ImportLog


logger = logging.getLogger(__name__)


class Command(BaseCommand):
    args = ''
    help = 'Imports a CSV of historic tariff prices'

    def add_arguments(self, parser):
        parser.add_argument('--csv')

    def handle(self, *args, **options):
        '''
        '''
        with open(options['csv'], 'r') as f:
            with transaction.atomic():
                month = None
                counter = 0
                for row in csv.DictReader(f):
                    month = datetime.strptime(row['Month'], '%d/%m/%Y')
                    counter += 1
                    if 'Category A' in row['DT Cat']:
                        tariff_category = 1
                    elif 'Category C' in row['DT Cat']:
                        tariff_category = 3
                    elif 'Category M' in row['DT Cat']:
                        tariff_category = 11
                    else:
                        raise
                    try:
                        vpid = DMDVmpp.objects.get(pk=row['VMPP']).vpid
                        product = DMDProduct.objects.get(vpid=vpid, concept_class=1)
                    except DMDVmpp.DoesNotExist:
                        logger.error(
                            "Could not find VMPP with id %s", row['VMPP'], exc_info=True)
                        continue
                    except DMDProduct.DoesNotExist:
                        logger.error(
                            "Could not find DMDProduct with vpid %s", vpid, exc_info=True)
                        continue
                    TariffPrice.objects.get_or_create(
                        date=month,
                        product=product,
                        vmpp_id=row['VMPP'],
                        tariff_category_id=tariff_category,
                        price_pence=int(row['DT Price']))
                ImportLog.objects.create(
                    category='tariff',
                    filename=options['csv'],
                    current_at=month)
