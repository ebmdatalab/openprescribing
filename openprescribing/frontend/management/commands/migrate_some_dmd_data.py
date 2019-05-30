# This is a one-off command to migrate all TariffPrice and NCSOConcession data
# from the dmd app to the frontend app.  It can be deleted once the dmd app has
# been removed.

from django.db import transaction
from django.core.management import BaseCommand

from dmd.models import TariffPrice as TariffPriceOld
from dmd.models import NCSOConcession as NCSOConcessionOld
from frontend.models import TariffPrice as TariffPriceNew
from frontend.models import NCSOConcession as NCSOConcessionNew


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        with transaction.atomic():
            TariffPriceNew.objects.all().delete()
            NCSOConcessionNew.objects.all().delete()

            TariffPriceNew.objects.bulk_create(
                TariffPriceNew(
                    date=tp_old.date,
                    vmpp_id=tp_old.vmpp_id,
                    tariff_category_id=tp_old.tariff_category_id,
                    price_pence=tp_old.price_pence,
                )
                for tp_old in TariffPriceOld.objects.all()
            )

            NCSOConcessionNew.objects.bulk_create(
                NCSOConcessionNew(
                    date=c_old.date,
                    vmpp_id=c_old.vmpp_id,
                    drug=c_old.drug,
                    pack_size=c_old.pack_size,
                    price_pence=c_old.price_concession_pence,
                )
                for c_old in NCSOConcessionOld.objects.all()
            )
