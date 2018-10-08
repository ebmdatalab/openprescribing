import csv
from datetime import datetime
from django.core.management import BaseCommand
from django.db import connection, transaction

from dmd2 import models


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('path')

    def handle(self, *args, **kwargs):
        type_to_model = {
            ('VMP', 'Presentation'): models.VMP,
            ('AMP', 'Presentation'): models.AMP,
            ('VMP', 'Pack'): models.VMPP,
            ('AMP', 'Pack'): models.AMPP,
        }

        with open(kwargs['path']) as f:
            reader = csv.DictReader(f)

            with transaction.atomic():
                for ix, row in enumerate(reader):
                    if ix % 10000 == 0:
                        print('{} {}'.format(datetime.now(), ix))
                    model = type_to_model[(row['VMP_AMP'], row['PACK_PRESENTATION'])]
                    snomed_id = row['SNOMED_CONCEPT_ID'].lstrip("'")
                    bnf_code = row['BNF_CODE'].lstrip("'")

                    if snomed_id == '':
                        # print('No SNOMED for {} {} {}'.format(row['VMP_AMP'], row['PACK_PRESENTATION'], bnf_code))
                        continue

                    if bnf_code == '':
                        # print('No BNF code for {} {} {}'.format(row['VMP_AMP'], row['PACK_PRESENTATION'], snomed_id))
                        continue

                    try:
                        obj = model.objects.get(id=snomed_id)
                    except model.DoesNotExist:
                        print('Could not get {} with id {}'.format(model.__name__, snomed_id))
                        continue
                    obj.bnf_code = bnf_code
                    obj.save()
