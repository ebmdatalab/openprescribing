import csv
import datetime
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

    def _run_tests(self, test, url, expected_total):
        r = requests.get(url)
        f = StringIO.StringIO(r.text)
        reader = csv.DictReader(f)
        all_rows = []
        for row in reader:
            all_rows.append(row)
        self.assertEqual(len(all_rows), expected_total)
        path = os.path.join(
            settings.PIPELINE_METADATA_DIR, 'smoketests', test + '.json')
        with open(path, 'rb') as f:
            expected = json.load(f)
            for i, row in enumerate(all_rows):
                self.assertEqual(
                    '%.2f' % float(row['actual_cost']), expected['cost'][i])
                self.assertEqual(row['items'], expected['items'][i])
                self.assertEqual(row['quantity'], expected['quantity'][i])


class TestSmokeTestSpendingByEveryone(SmokeTestBase):
    def test_presentation_by_all(self):
        url = '%s/api/1.0/spending/?format=csv&' % self.DOMAIN
        url += 'code=0501013B0AAAAAA'
        self._run_tests('presentation_by_all',
                        url,
                        PRESCRIBING_DATA_MONTHS)

    def test_chemical_by_all(self):
        url = '%s/api/1.0/spending/?format=csv&' % self.DOMAIN
        url += 'code=0407010F0'
        self._run_tests('chemical_by_all',
                        url,
                        PRESCRIBING_DATA_MONTHS)

    def test_bnf_section_by_all(self):
        url = '%s/api/1.0/spending/?format=csv&' % self.DOMAIN
        url += 'code=0702'
        self._run_tests('bnf_section_by_all',
                        url,
                        PRESCRIBING_DATA_MONTHS)


class TestSmokeTestSpendingByOnePractice(SmokeTestBase):
    def test_presentation_by_one_practice(self):
        url = '%s/api/1.0/spending_by_practice/?format=csv&' % self.DOMAIN
        url += 'code=0703021Q0BBAAAA&org=A81015'  # Cerazette 75mcg.
        self._run_tests('presentation_by_one_practice',
                        url,
                        PRESCRIBING_DATA_MONTHS)

    def test_chemical_by_one_practice(self):
        url = '%s/api/1.0/spending_by_practice/?' % self.DOMAIN
        url += 'format=csv&code=0212000AA&org=A81015'  # Rosuvastatin Calcium.
        self._run_tests('chemical_by_one_practice',
                        url,
                        PRESCRIBING_DATA_MONTHS)

    def test_multiple_chemicals_by_one_practice(self):
        url = '%s/api/1.0/spending_by_practice/?format=csv&' % self.DOMAIN
        url += 'code=0212000B0,0212000C0,0212000M0,0212000X0,0212000Y0'
        url += '&org=C85020'  # Multiple generic statins.
        self._run_tests('multiple_chemicals_by_one_practice',
                        url,
                        PRESCRIBING_DATA_MONTHS)

    def test_bnf_section_by_one_practice(self):
        url = '%s/api/1.0/spending_by_practice/' % self.DOMAIN
        url += '?format=csv&code=0304&org=L84077'
        self._run_tests('bnf_section_by_one_practice',
                        url,
                        PRESCRIBING_DATA_MONTHS)


class TestSmokeTestSpendingByCCG(SmokeTestBase):
    def test_presentation_by_one_ccg(self):
        url = '%s/api/1.0/spending_by_ccg?' % self.DOMAIN
        url += 'format=csv&code=0403030E0AAAAAA&org=10Q'
        self._run_tests('presentation_by_one_ccg',
                        url,
                        PRESCRIBING_DATA_MONTHS)

    def test_chemical_by_one_ccg(self):
        url = '%s/api/1.0/spending_by_ccg?' % self.DOMAIN
        url += 'format=csv&code=0212000AA&org=10Q'
        self._run_tests('chemical_by_one_ccg',
                        url,
                        PRESCRIBING_DATA_MONTHS)

    def test_bnf_section_by_one_ccg(self):
        url = '%s/api/1.0/spending_by_ccg?' % self.DOMAIN
        url += 'format=csv&code=0801&org=10Q'
        self._run_tests('bnf_section_by_one_ccg',
                        url,
                        PRESCRIBING_DATA_MONTHS)


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
