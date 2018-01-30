import logging
import os

from openpyxl import load_workbook
from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import connection, transaction

from dmd.models import DMDProduct
from gcutils.bigquery import Client


class Command(BaseCommand):
    help = ('Parse BNF->dm+d mapping supplied by NHSBSA and update tables'
            'accordingly.')

    def add_arguments(self, parser):
        parser.add_argument('--filename')

    def handle(self, *args, **options):
        filename = options['filename']

        if filename is None:
            base_dirname = os.path.join(settings.PIPELINE_DATA_BASEDIR, 'dmd_snomed')
            dirname = sorted(os.listdir(base_dirname))[-1]
            filenames = os.listdir(os.path.join(base_dirname, dirname))
            assert len(filenames) == 1
            filename = os.path.join(base_dirname, dirname, filenames[0])

        wb = load_workbook(filename=filename)
        rows = wb.active.rows

        headers = rows[0]
        assert headers[0].value.lower() == 'bnf code'
        assert headers[2].value.lower() == 'snomed code'

        with transaction.atomic():
            with connection.cursor() as cursor:
                for row in rows[1:]:  # skip header
                    bnf_code = row[0].value
                    snomed_code = row[2].value
                    sql = "UPDATE dmd_product SET BNF_CODE = %s WHERE DMDID = %s "
                    cursor.execute(sql.lower(), [bnf_code, snomed_code])
                    rowcount = cursor.rowcount
                    if not rowcount:
                        logging.warn(
                            "When adding BNF codes, could not find %s", snomed_code)

        Client('dmd').upload_model(DMDProduct)
