import os

from openpyxl import load_workbook
from django.core.management.base import BaseCommand
from django.db import connection, transaction


class Command(BaseCommand):
    help = ('Parse BNF->dm+d mapping supplied by NHSBSA and update tables'
            'accordingly.')

    def add_arguments(self, parser):
        parser.add_argument('--filename', required=True)

    def handle(self, *args, **options):
        wb = load_workbook(filename=os.path.join(options['filename']))
        rows = wb.active.rows
        with transaction.atomic():
            with connection.cursor() as cursor:
                for row in rows[1:]:  # skip header
                    bnf_code = row[0].value
                    snomed_code = row[4].value
                    sql = "UPDATE dmd_product SET BNF_CODE = %s WHERE DMDID = %s "
                    cursor.execute(sql.lower(), [bnf_code, snomed_code])
                    rowcount = cursor.rowcount
                    if not rowcount:
                        logging.warn(
                            "When adding BNF codes, could not find %s", snomed_code)
