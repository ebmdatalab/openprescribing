from django.test import TestCase

from frontend.models import Measure


class TitleCaseTests(TestCase):
    def test_variaous_cases(self):
        from common.utils import nhs_titlecase
        tests = [
            (
                'DR AS RAGHUNATH AND PTNRS',
                'Dr AS Raghunath and Ptnrs'
            ),
            (
                'OUT OF HOURS',
                'Out of Hours'
            ),
            (
                'NHS CORBY CCG',
                'NHS Corby CCG'
            ),
            (
                'CN HIV THREE BOROUGHS TEAM',
                'CN HIV Three Boroughs Team'
            ),
            (
                'DMC VICARAGE LANE',
                'DMC Vicarage Lane'
            ),
            (
                'DR CHEUNG KK PRACTICE',
                'Dr Cheung KK Practice'
            ),
            (
                'DR PM OPIE & DR AE SPALDING PRACTICE',
                'Dr PM Opie & Dr AE Spalding Practice'
            ),
            (
                'LUNDWOOD MEDICAL CENTRE PMS PRACTICE',
                'Lundwood Medical Centre PMS Practice'
            ),
            (
                "ST ANN'S MEDICAL CENTRE",
                "St Ann's Medical Centre"
            ),
            (
                "C&RH BIGGIN HILL",
                "C&RH Biggin Hill")
        ]
        for words, expected in tests:
            self.assertEquals(nhs_titlecase(words), expected)



class FunctionalTests(TestCase):
    fixtures = ['measures']

    def test_reconstructor_does_work(self):
        from django.db import connection
        from common.utils import constraint_and_index_reconstructor
        start_count = Measure.objects.count()
        with connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM pg_indexes")
            old_count = cursor.fetchone()[0]
            with constraint_and_index_reconstructor('frontend_measurevalue'):
                Measure.objects.all().delete()
                cursor.execute("SELECT COUNT(*) FROM pg_indexes")
                new_count = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM pg_indexes")
            after_count = cursor.fetchone()[0]
        self.assertLess(Measure.objects.count(), start_count)
        self.assertLess(new_count, old_count)
        self.assertEqual(old_count, after_count)
