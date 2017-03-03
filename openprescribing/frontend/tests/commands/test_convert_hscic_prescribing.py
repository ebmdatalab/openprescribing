import csv
import os
import unittest
from django.core.management import call_command
from django.test import TestCase


class CommandsTestCase(TestCase):

    @unittest.skipIf("TRAVIS" in os.environ and os.environ["TRAVIS"],
                     "Skipping this test on Travis CI.")
    def test_import_hscic_prescribing(self):
        args = []
        test_file = 'frontend/tests/fixtures/commands/'
        test_file += 'hscic_prescribing_sample.csv'
        opts = {
            'filename': test_file,
            'is_test': True
        }
        call_command('convert_hscic_prescribing', *args, **opts)

        test_output = 'frontend/tests/fixtures/commands/'
        test_output += 'hscic_prescribing_sample_test.CSV'
        reader = csv.reader(open(test_output, 'rU'))
        rows = []
        for row in reader:
            rows.append(row)

        os.remove(test_output)
        self.assertEqual(len(rows), 51)

        # Test the basics are in the order expected by our COPY statement:
        # pct_id,practice_id,presentation_code,
        # total_items,actual_cost,
        # quantity,processing_date,price_per_unit
        self.assertEqual(rows[0][0], 'RXA')
        self.assertEqual(rows[0][1], 'N81646')
        self.assertEqual(rows[0][2], '0102000N0AAABAB')
        self.assertEqual(rows[0][3], '1')
        self.assertEqual(rows[0][4], '0.7')
        self.assertEqual(rows[0][5], '12')
        self.assertEqual(rows[0][6], '2014-10-01')
