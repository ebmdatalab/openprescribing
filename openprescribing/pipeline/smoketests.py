from datetime import datetime
import csv
import json
import StringIO
import os
import requests
import unittest

from django.conf import settings

'''
Run smoke tests against live site. 35 separate tests to run.
Spending BY: one practice, multiple practices, one CCG,
multiple CCGs, all
Spending ON: one presentation, multiple presentations, one chemical,
multiple chemicals, one section, multiple sections, all
The expected numbers are generated from pipeline/misc/smoke.sh
'''

PRESCRIBING_DATA_MONTHS = 5 * 12


class SmokeTestBase(unittest.TestCase):

    DOMAIN = 'https://openprescribing.net'

    def _now_date(self):
        if 'LAST_IMPORTED' in os.environ:
            now = datetime.strptime(os.environ['LAST_IMPORTED'], "%Y_%m")
        else:
            now = datetime.now()
        return now

    def _run_tests(self, test_name, path_fragment, params):
        url = '{}/api/1.0/{}/'.format(self.DOMAIN, path_fragment)
        params['format'] = 'csv'
        r = requests.get(url, params=params)
        f = StringIO.StringIO(r.text)
        all_rows = list(csv.DictReader(f))
        self.assertEqual(len(all_rows), PRESCRIBING_DATA_MONTHS)

        path = os.path.join(
            settings.PIPELINE_METADATA_DIR, 'smoketests', test_name + '.json')

        with open(path, 'rb') as f:
            expected = json.load(f)

        for i, row in enumerate(all_rows):
            # Expected values come from querying BQ and so values for `items`
            # and `quantity` are integers, and value for `actual_cost` is a
            # string representing a number with at most two decimial places.
            # Actual values come from a CSV file and so need to be converted to
            # the correct type for comparison.

            self.assertAlmostEqual(
                float(row['actual_cost']),
                float(expected['cost'][i]),
                places=2
            )
            self.assertEqual(
                int(row['items']),
                expected['items'][i]
            )
            self.assertEqual(
                int(row['quantity']),
                expected['quantity'][i]
            )


class TestSmokeTestSpendingByEveryone(SmokeTestBase):
    def test_presentation_by_all(self):
        params = {'code': '0501013B0AAAAAA'}
        self._run_tests('presentation_by_all', 'spending', params)

    def test_chemical_by_all(self):
        params = {'code': '0407010F0'}
        self._run_tests('chemical_by_all', 'spending', params)

    def test_bnf_section_by_all(self):
        params = {'code': '0702'}
        self._run_tests('bnf_section_by_all', 'spending', params)


class TestSmokeTestSpendingByOnePractice(SmokeTestBase):
    def test_presentation_by_one_practice(self):
        params = {'code': '0703021Q0BBAAAA', 'org': 'A81015'}  # Cerazette 75mcg.
        self._run_tests(
            'presentation_by_one_practice',
            'spending_by_practice',
            params
        )

    def test_chemical_by_one_practice(self):
        params = {'code': '0212000AA', 'org': 'A81015'}  # Rosuvastatin Calcium.
        self._run_tests(
            'chemical_by_one_practice',
            'spending_by_practice',
            params
        )

    def test_multiple_chemicals_by_one_practice(self):
        # Multiple generic statins.
        params = {
            'code': '0212000B0,0212000C0,0212000M0,0212000X0,0212000Y0',
            'org': 'C85020',
        }
        self._run_tests(
            'multiple_chemicals_by_one_practice',
            'spending_by_practice',
            params
        )

    def test_bnf_section_by_one_practice(self):
        params = {'code': '0304', 'org': 'L84077'}
        self._run_tests(
            'bnf_section_by_one_practice',
            'spending_by_practice',
            params
        )


class TestSmokeTestSpendingByCCG(SmokeTestBase):
    def test_presentation_by_one_ccg(self):
        params = {'code': '0403030E0AAAAAA', 'org': '10Q'}
        self._run_tests('presentation_by_one_ccg', 'spending_by_ccg', params)

    def test_chemical_by_one_ccg(self):
        params = {'code': '0212000AA', 'org': '10Q'}
        self._run_tests('chemical_by_one_ccg', 'spending_by_ccg', params)

    def test_bnf_section_by_one_ccg(self):
        params = {'code': '0801', 'org': '10Q'}
        self._run_tests('bnf_section_by_one_ccg', 'spending_by_ccg', params)


class TestSmokeTestMeasures(SmokeTestBase):

    '''
    Smoke tests for all 13 KTTs, for the period July-Sept 2015.
    Cross-reference against data from the BSA site.
    NB BSA calculations are done over a calendar quarter, and ours are done
    monthly, so sometimes we have to multiply things to get the same answers.
    '''

    def get_data_for_q3_2015(self, data):
        total = {
            'numerator': 0,
            'denominator': 0
        }
        for d in data:
            if (d['date'] == '2015-07-01') or \
               (d['date'] == '2015-08-01') or \
               (d['date'] == '2015-09-01'):
                total['numerator'] += d['numerator']
                total['denominator'] += d['denominator']
        total['calc_value'] = (
            total['numerator'] / float(total['denominator'])) * 100
        return total

    def retrieve_data_for_measure(self, measure, practice):
        self.DOMAIN = 'https://openprescribing.net'
        url = '%s/api/1.0/measure_by_practice/?format=json&' % self.DOMAIN
        url += 'measure=%s&org=%s' % (measure, practice)
        r = requests.get(url)
        data = json.loads(r.text)
        rows = data['measures'][0]['data']
        return self.get_data_for_q3_2015(rows)

    def test_measure_by_practice(self):
        q = self.retrieve_data_for_measure(
            'ktt3_lipid_modifying_drugs', 'A81001')
        bsa = {
            'numerator': 34,
            'denominator': 1265,
            'calc_value': '2.688'
        }
        self.assertEqual(q['numerator'], bsa['numerator'])
        self.assertEqual(q['denominator'], bsa['denominator'])
        self.assertEqual("%.3f" % q['calc_value'], bsa['calc_value'])

        q = self.retrieve_data_for_measure('ktt9_antibiotics', 'A81001')
        bsa = {
            'numerator': 577,
            'denominator': 7581.92,  # BSA's actual STAR-PU value is 7509
            'calc_value': (577 / 7581.92) * 100
        }
        self.assertEqual(q['numerator'], bsa['numerator'])
        self.assertEqual(
            "%.0f" % q['denominator'], "%.0f" % bsa['denominator'])
        self.assertEqual("%.2f" % q['calc_value'], "%.2f" % bsa['calc_value'])

        q = self.retrieve_data_for_measure('ktt9_cephalosporins', 'A81001')
        bsa = {
            'numerator': 30,
            'denominator': 577,
            'calc_value': '5.199'
        }
        self.assertEqual(q['numerator'], bsa['numerator'])
        self.assertEqual(q['denominator'], bsa['denominator'])
        self.assertEqual("%.3f" % q['calc_value'], bsa['calc_value'])

        q = self.retrieve_data_for_measure('ktt12_diabetes_insulin', 'A81001')
        bsa = {
            'numerator': 44,
            'denominator': 64,
            'calc_value': '68.750'
        }
        self.assertEqual(q['numerator'], bsa['numerator'])
        self.assertEqual(q['denominator'], bsa['denominator'])
        self.assertEqual("%.3f" % q['calc_value'], bsa['calc_value'])

        q = self.retrieve_data_for_measure('ktt13_nsaids_ibuprofen', 'A81001')
        bsa = {
            'denominator': 413,
            'numerator': 57,
            'calc_value': '13.801'
        }
        self.assertEqual(q['numerator'], bsa['numerator'])
        self.assertEqual(q['denominator'], bsa['denominator'])
        self.assertEqual("%.3f" % q['calc_value'], bsa['calc_value'])

    def test_total_measures(self):
        url = self.DOMAIN + '/api/1.0/measure/?format=json'
        result = requests.get(url).json()
        for m in result['measures']:
            last_date = sorted([x['date'] for x in m['data']])[-1]
            expected = self._now_date().strftime('%Y-%m-%d')
            msg = "Expected last date of %s for %s; got %s" % (
                expected, m['id'], last_date)
            self.assertEqual(
                last_date, expected, msg)


if __name__ == '__main__':
    unittest.main()
