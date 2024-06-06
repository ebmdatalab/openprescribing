from django.core.management import BaseCommand, CommandError
from django.db import transaction
from dmd.models import VMPP
from frontend.models import NCSOConcession


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument("concession_id")
        parser.add_argument("vmpp_id")

    def handle(self, *args, **kwargs):
        try:
            concession = NCSOConcession.objects.get(id=kwargs["concession_id"])
        except NCSOConcession.DoesNotExist:
            raise CommandError("Could not find concession")

        try:
            vmpp = VMPP.objects.get(id=kwargs["vmpp_id"])
        except VMPP.DoesNotExist:
            raise CommandError("Could not find VMPP")

        try:
            existing = NCSOConcession.objects.get(date=concession.date, vmpp=vmpp)
        except NCSOConcession.DoesNotExist:
            existing = None

        if existing is None:
            concession.vmpp = vmpp
            concession.save()
        else:
            # If we've previously correctly imported a concession for this VMPP and this
            # month then we can't just set the VMPP on the new object and save it as
            # this violates the uniqueness constraint. Instead we have to update the
            # existing object and delete this one.
            existing.drug = concession.drug
            existing.pack_size = concession.pack_size
            existing.price_pence = concession.price_pence
            with transaction.atomic():
                existing.save()
                concession.delete()
            concession = existing

        print(
            "Reconciled `{}` against `{}`".format(
                concession.drug_and_pack_size, vmpp.nm
            )
        )
