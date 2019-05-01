from __future__ import print_function

import json
import os
import openpyxl as op
import re
from django.conf import settings
from django.core.management.base import BaseCommand
import sys


class Command(BaseCommand):
    args = ''
    help = 'Calculate STAR-PU weights from HSCIC Excel file. '
    help += 'Save weights into frontend app, in preparation for '
    help += 'calculating STAR-PUs on PracticeStatistics save method. '
    help += 'Re-run when the HSCIC updates its file. '

    def add_arguments(self, parser):
        parser.add_argument('--filename')

    def handle(self, *args, **options):
        self.IS_VERBOSE = False
        if options['verbosity'] > 1:
            self.IS_VERBOSE = True
        if not options['filename']:
            print('Please supply a filename')
            sys.exit()
        fname = options['filename']
        f = op.load_workbook(fname)
        sheet = f['STAR-PUs']
        idxs = self.get_sect_cells('A6')
        ranges = []
        for ix in idxs:
            ranges.append(self.get_cells_range(ix))
        weights = {}
        for idx, cell_range in ranges:
            m = re.sub(r'\(.+?\)\s*', '', str(sheet[idx].value))
            m = m.replace(' based STAR PU', '').replace('  ', ' ').strip()
            m = m.replace(' ', '_').replace('&', 'and').lower()
            weights[m] = self.parse_weight(sheet, cell_range)

        path = os.path.join(settings.APPS_ROOT, 'frontend',
                            'star_pu_weights.json')
        with open(path, 'w') as outfile:
            json.dump(weights, outfile, sort_keys=True, indent=4)

    def get_sect_cells(self, first_cell):
        """
        There are 25 different weights at 15-line intervals.
        Fetch the contents of those cells.
        """
        sectionlist = []
        res = re.match(r"([A-Z])([0-9]+)$", first_cell)
        for i in range(25):
            sectionlist.append(res.group(1) + str(int(res.group(2)) + 15 * i))
        return sectionlist

    def get_cells_range(self, idx):
        '''
        For each title cell, find the range of cells containing weights.
        '''
        res = re.match(r"([A-Z])([0-9]+)$", idx)
        first = chr(ord(res.group(1)) + 2) + str(int(res.group(2)) + 3)
        last = chr(ord(res.group(1)) + 4) + str(int(res.group(2)) + 11)
        return (idx, first + ':' + last)

    def parse_weight(self, sheet, cell_range):
        weight = {}
        for age, m, f in sheet[cell_range]:
            weight[age.value] = (m.value, f.value)
        return weight
