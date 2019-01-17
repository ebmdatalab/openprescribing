from datetime import datetime
from django.core.management import BaseCommand
from django.db import connection, transaction
from openpyxl import load_workbook

from dmd2 import models


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('path')

    def handle(self, *args, **kwargs):
        type_to_model = {
            ('Presentation', 'VMP'): models.VMP,
            ('Presentation', 'AMP'): models.AMP,
            ('Pack', 'VMP'): models.VMPP,
            ('Pack', 'AMP'): models.AMPP,
        }

        wb = load_workbook(filename=kwargs['path'])
        rows = wb.active.rows

        headers = next(rows)
        assert headers[0].value == 'Presentation / Pack Level'
        assert headers[1].value == 'VMP / AMP'
        assert headers[2].value == 'BNF Code'
        assert headers[4].value == 'SNOMED Code'

        with transaction.atomic():
            models.VMP.objects.update(bnf_code=None)
            models.AMP.objects.update(bnf_code=None)
            models.VMPP.objects.update(bnf_code=None)
            models.AMPP.objects.update(bnf_code=None)

            for ix, row in enumerate(rows):
                if ix % 10000 == 0:
                    print('{} {}'.format(datetime.now(), ix))

                model = type_to_model[(row[0].value, row[1].value)]

                bnf_code = row[2].value
                snomed_id = row[4].value

                if bnf_code is None or snomed_id is None:
                    continue

                if bnf_code == "'" or snomed_id == "'":
                    continue

                bnf_code = bnf_code.lstrip("'")
                snomed_id = snomed_id.lstrip("'")

                try:
                    obj = model.objects.get(id=snomed_id)
                except model.DoesNotExist:
                    print('Could not get {} with id {}'.format(model.__name__, snomed_id))
                    continue
                obj.bnf_code = bnf_code
                obj.save()
