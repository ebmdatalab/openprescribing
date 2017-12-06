from datetime import datetime
import io
import logging
import re

from backports import csv

from django.core.management import BaseCommand
from django.db import transaction

from dmd.models import DMDProduct
from dmd.models import DMDVmpp
from frontend.models import ImportLog
from dmd.models import TariffPrice


logger = logging.getLogger(__name__)


def get_tariff_cat_id(cat):
    if 'Category A' in cat:
        tariff_category = 1
    elif 'Category C' in cat:
        tariff_category = 3
    elif 'Category M' in cat:
        tariff_category = 11
    else:
        raise
    return tariff_category


def get_product_id(vmpp):
    try:
        vpid = DMDVmpp.objects.get(pk=vmpp).vpid
        product = DMDProduct.objects.get(vpid=vpid, concept_class=1)
        return product.pk
    except DMDVmpp.DoesNotExist:
        logger.exception("Could not find VMPP with id %s", vmpp, exc_info=True)
    except DMDProduct.DoesNotExist:
        logger.exception("Could not find DMD product with VPID %s", vpid, exc_info=True)


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('--filename', required=True)

    def handle(self, *args, **kwargs):
        filename = kwargs['filename']

        match = re.search('drug_tariff_(\d{4}_\d{2}).csv', filename)
        year_and_month = match.groups()[0]
        date = datetime.strptime(year_and_month + "_01", "%Y_%m_%d")
        with io.open(filename, encoding='utf8') as f:
            rows = list(csv.DictReader(f))
        with transaction.atomic():
            for d in rows:
                vmpp = d['vmpp']
                product_id = get_product_id(d['vmpp'])
                dt_cat = get_tariff_cat_id(d['tariff_category'])
                price_pence = d['price_pence']
                TariffPrice.objects.get_or_create(
                    date=date,
                    vmpp_id=vmpp,
                    product_id=product_id,
                    tariff_category_id=dt_cat,
                    price_pence=price_pence
                )
            ImportLog.objects.create(
                category='tariff',
                filename=kwargs['filename'],
                current_at=date)
