from django.test import TestCase

from frontend.models import Measure


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
