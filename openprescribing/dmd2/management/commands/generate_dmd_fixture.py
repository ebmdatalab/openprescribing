'''
This generates a self-consistent fixture containing the given dm+d objects and
any related objects.

For instance, to generate a fixture containing a VMPP, the fixture must also
include the VMPP's VMP, as well as instances of anything that VMPPs and VMPs
have foreign keys to, such as UnitOfMeasure or VTM.
'''

from django.core import serializers
from django.core.management import BaseCommand
from django.db.models.fields.related import ForeignKey

from dmd2.models import VMP, VMPP, AMP, AMPP


class Command(BaseCommand):
    help = __doc__

    def add_arguments(self, parser):
        parser.add_argument('ids', nargs='+')

    def handle(self, *args, **kwargs):
        ids = kwargs['ids']
        objs = []
        objs.extend(VMP.objects.filter(id__in=ids))
        objs.extend(VMPP.objects.filter(id__in=ids))
        objs.extend(AMP.objects.filter(id__in=ids))
        objs.extend(AMPP.objects.filter(id__in=ids))

        for obj in objs:
            for f in obj._meta.fields:
                if isinstance(f, ForeignKey):
                    related_obj = getattr(obj, f.name)
                    if related_obj is not None and related_obj not in objs:
                        objs.append(related_obj)

        print(serializers.serialize('json', objs, indent=2))
