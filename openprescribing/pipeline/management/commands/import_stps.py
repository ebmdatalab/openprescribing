import csv
import re

from django.core.management import BaseCommand
from django.db import transaction
from frontend.models import PCT, RegionalTeam, STP

from openpyxl import load_workbook


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('--filename')

    def handle(self, *args, **kwargs):
        wb = load_workbook(kwargs['filename'])
        sheet = wb.get_sheet_by_name('Current STPs')

        assert sheet['A5'].value == 'NHS England Region', sheet['A5'].value
        assert sheet['B5'].value == 'ODS STP Code', sheet['B5'].value
        assert sheet['D5'].value == 'ONS STP Code', sheet['D5'].value
        assert sheet['E5'].value == 'STP Name', sheet['E5'].value
        assert sheet['J5'].value == 'CCG', sheet['J5'].value
        assert sheet['K5'].value == 'ODS CCG Code', sheet['K5'].value

        data = [[cell.value for cell in row] for row in sheet.rows]

        with transaction.atomic():
            for row in data[5:]:
                if not row[10]:
                    continue

                rt_code = re.search('\((\w{3})\)', row[0]).groups()[0]
                rt = RegionalTeam.objects.get(code=rt_code)

                stp_code = row[1]
                stp_ons_code = row[3]
                stp_name = row[4].strip()
                stp, _ = STP.objects.get_or_create(ons_code=stp_ons_code)
                stp.code = stp_code
                if stp_name:
                    # The stp_name is only present in the first row that an STP appears!
                    stp.name = stp_name
                stp.regional_team = rt
                stp.save()

                ccg_code = row[10]
                ccg = PCT.objects.get(code=ccg_code)
                assert ccg.regional_team == rt
                print ccg.name, 'is in STP', stp.name
                ccg.stp = stp
                ccg.save()
