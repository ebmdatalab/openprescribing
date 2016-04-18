import csv
import re
import sys
from django.core.exceptions import ObjectDoesNotExist
from django.core.management.base import BaseCommand, CommandError
from frontend.models import Presentation


class Command(BaseCommand):
    args = ''
    help = 'Imports ADQ codes.'

    def add_arguments(self, parser):
        parser.add_argument('--filename')

    def handle(self, *args, **options):
        '''
        Import BNF numbered chapters, sections and paragraphs.
        '''
        if not options['filename']:
            print 'Please supply a filename'
            sys.exit()

        p = Presentation.objects.all()

        reader = csv.DictReader(open(options['filename'], 'rU'))
        for row in reader:
            code = row['BNF Code']
            try:
                adq = row['ADQ Value'].strip()
                if adq == 'N/A':
                    continue
                p = Presentation.objects.get(bnf_code=code)
                adq_unit = row['ADQ Unit'].strip().lower()
                active_quantity = self.get_active_quantity(row['BNF Name'], adq_unit)
                p.active_quantity = active_quantity
                p.adq = adq
                p.adq_unit = adq_unit
                if active_quantity:
                    p.percent_of_adq = (float(active_quantity) / float(p.adq))
                else:
                    p.percent_of_adq = None
                p.save()
            except ObjectDoesNotExist:
                pass

    def get_active_quantity(self, bnf_name, adq_unit):
        bnf_name = bnf_name.lower()
        if adq_unit:
            digits = re.findall('\d+' + adq_unit, bnf_name)
        else:
            digits = re.findall('\d+', bnf_name)
        if digits:
            return digits[0].replace(adq_unit, '')
        else:
            return None

