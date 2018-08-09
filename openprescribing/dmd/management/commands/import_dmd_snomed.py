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
        assert headers[0].value == 'BNF Code'
        assert headers[2].value == 'VMPP / AMPP SNOMED Code'

        num_amp_matches = 0
        num_vmp_matches = 0
        num_no_matches = 0

        # Each row of the spreadsheet contains a BNF code and a SNOMED code
        # which is an ID of either a AMPP or an VMPP.  (There are lots of rows
        # without a BNF code, and a handful without a SNOMED code, and we
        # ignore these.)
        #
        # The only way to find out whether a SNOMED code is an AMPP ID or a
        # VMPP ID is to query the AMPP and VMPP tables in turn.  We know that
        # there is no overlap between AMPP IDs and VMPP IDs, so if we find an
        # AMPP with a given SNOMED code, we know there won't be a VMPP with the
        # same SNOMED code.
        #
        # Our dmd_product table contains AMPs and VMPs, and has a field `dmdid`
        # which is the ID of the corresponding AMP or VMP.  If the SNOMED code
        # is for an AMPP we can retrieve the corresponding AMP ID, and if it is
        # for a VMPP we can retrieve the corresponding VMP ID.  We can use this
        # to update the bnf_code field in the dmd_product table.

        with transaction.atomic():
            with connection.cursor() as cursor:
                for row in rows[1:]:
                    bnf_code = row[0].value
                    if not bnf_code:
                        continue

                    if bnf_code[0] == "'":
                        bnf_code = bnf_code[1:]

                    snomed_code = row[2].value
                    if not snomed_code:
                        continue

                    if snomed_code[0] == "'":
                        snomed_code = snomed_code[1:]
                        if not snomed_code:
                            continue

                    dmdid = None

                    cursor.execute(
                        'SELECT apid FROM dmd_ampp WHERE appid = %s',
                        [snomed_code]
                    )
                    rows = cursor.fetchall()

                    if rows:
                        # snomed_code is an AMPP ID
                        assert len(rows) == 1
                        dmdid = rows[0][0]
                        num_amp_matches += 1

                    else:
                        cursor.execute(
                            'SELECT vpid FROM dmd_vmpp WHERE vppid = %s',
                            [snomed_code]
                        )
                        rows = cursor.fetchall()

                        if rows:
                            # snomed_code is an VMPP ID
                            assert len(rows) == 1
                            dmdid = rows[0][0]
                            num_vmp_matches += 1

                        else:
                            num_no_matches += 1

                    if dmdid is not None:
                        cursor.execute(
                            'UPDATE dmd_product SET bnf_code = %s WHERE dmdid = %s',
                            [bnf_code, dmdid]
                        )

        print('Rows matching AMPs:', num_amp_matches)
        print('Rows matching VMPs:', num_vmp_matches)
        print('Rows matching nothing:', num_no_matches)

        Client('dmd').upload_model(DMDProduct)
