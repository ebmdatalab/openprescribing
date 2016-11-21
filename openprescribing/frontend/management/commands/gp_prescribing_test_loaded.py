import csv
import os
from django.core.management.base import BaseCommand, CommandError
from frontend.models import SHA, PCT, Practice, Chemical, Prescription
from django.db.models import Sum


class Command(BaseCommand):
    args = ''
    help = 'Tests that the data looks how we expect it to, '
    help += 'based on the HSCIC data files. '
    help += 'Will be slow to run as lots of index-only scans.'

    def handle(self, *args, **options):
        self.test_total_row_count()
        self.test_rows_by_practice()
        self.test_rows_by_ccg()
        self.test_rows_by_bnf_section()
        self.test_rows_by_chemical()
        self.test_rows_by_presentation()

    def test_total_row_count(self):
        '''
        Test there are the total number of prescriptions we expect, per month
        '''
        filepath = os.path.dirname(os.path.abspath(__file__))
        filename = filepath + '/gp_prescribing_count_by_month.csv'
        reader = csv.DictReader(open(filename, 'rU'))
        for row in reader:
            month = row['month'] + '-01'
            print 'Checking prescriptions for %s' % month
            prescriptions = Prescription.objects.filter(processing_date=month)
            print 'row count', int(row['count'])
            print 'prescriptions count', prescriptions.count()
            assert int(row['count']) == prescriptions.count()

    def test_rows_by_practice(self):
        '''
        Test that the row count, and the summed values, for a
        particular practice look OK.
        TODO: Use our materialized views to test a big practice,
        use our Django items to test a small practice.
        '''
        practice = Practice.objects.get(code='P87659')
        prescriptions = Prescription.objects.filter(practice=practice)
        assert prescriptions.count() == 1234
        total_items = prescriptions.aggregate(Sum('total_items'))
        assert total_items == 12345
        actual_cost = prescriptions.aggregate(Sum('actual_cost'))
        assert actual_cost == 12345
        quantity = prescriptions.aggregate(Sum('quantity'))
        assert quantity == 12345

    def test_rows_by_ccg(self):
        '''
        Test that the row count, and the summed values, for a
        two selected CCGs looks OK.
        Data based on download from HSCIC iView.
        TODO: Use our materialized views for this
        '''
        practice = PCT.objects.get(code='P87659')
        prescriptions = Prescription.objects.filter(pct=pct)
        assert prescriptions.count() == 1234
        total_items = prescriptions.aggregate(Sum('total_items'))
        assert total_items == 12345
        actual_cost = prescriptions.aggregate(Sum('actual_cost'))
        assert actual_cost == 12345
        quantity = prescriptions.aggregate(Sum('quantity'))
        assert quantity == 12345

    def test_rows_by_bnf_section(self):
        '''
        Test that the row count, and the summed values, for a
        particular BNF section look OK.
        Data based on download from HSCIC iView.
        '''
        pass

    def test_rows_by_chemical(self):
        '''
        Test that the row count, and the summed values, for a
        particular chemical look OK.
        Data based on download from HSCIC iView.
        '''
        pass

    def test_rows_by_presentation(self):
        '''
        Test that the row count, and the summed values, for a
        particular presentation look OK.
        Data based on download from HSCIC iView.
        '''
        pass
