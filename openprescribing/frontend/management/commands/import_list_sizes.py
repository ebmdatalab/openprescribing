import csv
import glob
from datetime import datetime
from django.core.management.base import BaseCommand, CommandError
from django.core.exceptions import ObjectDoesNotExist
from frontend.models import Practice, PracticeStatistics, PCT


class Command(BaseCommand):
    args = ''
    help = 'Imports list size information. '
    help += 'Filename should be in the format '
    help += 'Patient_List_Size_YYYY_M1-M1.csv '
    help += 'where M1 is the first month in the quarter '
    help += 'and M2 is the last month in the quarter. '
    help += 'For example, Patient_List_Size_2014_06-09.csv'

    def add_arguments(self, parser):
        parser.add_argument('--filename')

    def handle(self, *args, **options):
        self.IS_VERBOSE = False
        if options['verbosity'] > 1:
            self.IS_VERBOSE = True
        if options['filename']:
            filenames = [options['filename']]
        else:
            filenames = glob.glob('data/list_sizes/Patient_List_Size*.csv')
        for f in filenames:
            if self.IS_VERBOSE:
                print f
            entries = csv.DictReader(open('%s' % f, 'rU'))
            if 'Month' in entries.fieldnames:
                # This is the BSA's multi-year data: we don't need to
                # derive the months from the filename.
                for row in entries:
                    m = row['Month'].split('/')
                    m.reverse()
                    month = '20' + '-'.join(m)
                    self.process_row(row, month)
            else:
                months = self.get_months_from_filename(f)
                for row in entries:
                    for m in months:
                        self.process_row(row, m)

    def get_months_from_filename(self, filename):
        f = filename.replace('.csv', '').split('_')
        year = f[-2]
        first_month = int(f[-1].split('-')[0])
        months = []
        for i in range(0, 3):
            month = first_month + i
            months.append('%s-%s-01' % (year, month))
        return months

    def process_row(self, row, month):
        prac_code = row['Practice Code']
        pct_code = row['PCO Code'][:3]
        try:
            practice = Practice.objects.get(code=prac_code)
        except Practice.DoesNotExist:
            return
        try:
            pct = PCT.objects.get(code=pct_code)
        except PCT.DoesNotExist:
            pct = None
        try:
            prac_list = PracticeStatistics.objects.get(
                practice=practice,
                pct=pct,
                date=month
            )
            prac_list.male_0_4 = int(row['Male 0-4'])
            prac_list.female_0_4 = int(row['Female 0-4'])
            prac_list.male_5_14 = int(row['Male 5-14'])
            prac_list.female_5_14 = int(row['Female 5-14'])
            prac_list.male_15_24 = int(row['Male 15-24'])
            prac_list.female_15_24 = int(row['Female 15-24'])
            prac_list.male_25_34 = int(row['Male 25-34'])
            prac_list.female_25_34 = int(row['Female 25-34'])
            prac_list.male_35_44 = int(row['Male 35-44'])
            prac_list.female_35_44 = int(row['Female 35-44'])
            prac_list.male_45_54 = int(row['Male 45-54'])
            prac_list.female_45_54 = int(row['Female 45-54'])
            prac_list.male_55_64 = int(row['Male 55-64'])
            prac_list.female_55_64 = int(row['Female 55-64'])
            prac_list.male_65_74 = int(row['Male 65-74'])
            prac_list.female_65_74 = int(row['Female 65-74'])
            prac_list.male_75_plus = int(row['Male 75+'])
            prac_list.female_75_plus = int(row['Female 75+'])
            prac_list.save()
        except ObjectDoesNotExist:
            prac_list = PracticeStatistics.objects.create(
                practice=practice,
                pct=pct,
                date=month,
                male_0_4=int(row['Male 0-4']),
                female_0_4=int(row['Female 0-4']),
                male_5_14=int(row['Male 5-14']),
                female_5_14=int(row['Female 5-14']),
                male_15_24=int(row['Male 15-24']),
                female_15_24=int(row['Female 15-24']),
                male_25_34=int(row['Male 25-34']),
                female_25_34=int(row['Female 25-34']),
                male_35_44=int(row['Male 35-44']),
                female_35_44=int(row['Female 35-44']),
                male_45_54=int(row['Male 45-54']),
                female_45_54=int(row['Female 45-54']),
                male_55_64=int(row['Male 55-64']),
                female_55_64=int(row['Female 55-64']),
                male_65_74=int(row['Male 65-74']),
                female_65_74=int(row['Female 65-74']),
                male_75_plus=int(row['Male 75+']),
                female_75_plus=int(row['Female 75+'])
                )
