from __future__ import print_function

from django.core.management import BaseCommand, CommandError

from dmd2.models import VMPP
from frontend.models import NCSOConcession


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('concession_id')
        parser.add_argument('vmpp_id')

    def handle(self, *args, **kwargs):
        try:
            concession = NCSOConcession.objects.get(id=kwargs['concession_id'])
        except NCSOConcession.DoesNotExist:
            raise CommandError('Could not find concession')

        try:
            vmpp = VMPP.objects.get(id=kwargs['vmpp_id'])
        except VMPP.DoesNotExist:
            raise CommandError('Could not find VMPP')

        concession.vmpp = vmpp
        concession.save()

        print('Reconciled `{}` against `{}`'.format(
            concession.drug_and_pack_size, vmpp.nm))
