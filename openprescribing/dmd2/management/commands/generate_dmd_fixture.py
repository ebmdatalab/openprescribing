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
from django.db.models.fields.reverse_related import ManyToOneRel, OneToOneRel

from dmd2.models import VMP, VMPP, AMP, AMPP


class Command(BaseCommand):
    help = __doc__

    def add_arguments(self, parser):
        parser.add_argument('ids', nargs='+')
        parser.add_argument('--include-reverse-relations', action='store_true')

    def handle(self, *args, **kwargs):
        classes_we_care_about = (VMP, VMPP, AMP, AMPP)
        ids = kwargs['ids']
        objs = []
        for cls in classes_we_care_about:
            objs.extend(cls.objects.filter(id__in=ids))

        for obj in objs:
            for f in obj._meta.get_fields():
                if isinstance(f, ForeignKey):
                    related_obj = getattr(obj, f.name)
                    if related_obj is not None and related_obj not in objs:
                        objs.append(related_obj)

                if (
                        kwargs['include_reverse_relations']
                        and isinstance(obj, classes_we_care_about)
                        and isinstance(f, ManyToOneRel)
                        and f.related_model in classes_we_care_about
                    ):
                    related_objs = getattr(obj, f.get_accessor_name()).all()
                    for related_obj in related_objs:
                        if related_obj not in objs:
                            objs.append(related_obj)

        print(serializers.serialize('json', objs, indent=2))
