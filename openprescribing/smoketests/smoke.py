import csv
import StringIO
import requests
import unittest

'''
Run smoke tests against live site. 35 separate tests to run.
Spending BY: one practice, multiple practices, one CCG,
multiple CCGs, all
Spending ON: one presentation, multiple presentations, one chemical,
multiple chemicals, one section, multiple sections, all
The expected numbers are generated from smoke.sh
'''


class SmokeTestBase(unittest.TestCase):

    DOMAIN = 'https://openprescribing.net'
    NUM_RESULTS = 60  # Should equal number of months since Aug 2010.


class TestSmokeTestSpendingByEveryone(SmokeTestBase):

    def test_all_spending(self):
        pass

    def test_presentation_by_all(self):
        pass
        # url = '%s/api/1.0/spending?' % self.DOMAIN
        # url += 'code=1106000L0AAAAAA'  # Latanoprost_Eye Dps 50mcg/ml
        # r = requests.get(url)
        # f = StringIO.StringIO(r.text)
        # reader = csv.DictReader(f)
        # all_rows = []
        # for row in reader:
        #     all_rows.append(row)

        # self.assertEqual(len(all_rows), 56)
        # june_2013 = all_rows[34]
        # self.assertEqual(june_2013['row_name'], 'All practices in England')

        # expected = {
        #     'cost': ['2718454.49', '2875832.96', '2723283.51', '2784760.31', '2741188.43',
        #              '2689659.68', '2489674.14', '2851228.36', '2558381.66', '2747539.41', '2790905.36',
        #              '2731594.30', '2786513.67', '2861122.25', '2686434.85', '2781840.72', '2898971.25',
        #              '2685110.57', '2677922.85', '2933481.09', '2730045.92', '2629264.88', '2422668.25',
        #              '1032767.99', '1076314.41', '999838.59', '953452.47', '942549.89', '933842.92',
        #              '791364.92', '715460.27', '774804.40', '664737.32', '700500.12', '645263.63',
        #              '581314.22', '573793.94', '553160.36', '524812.98', '503777.67', '518198.71',
        #              '525985.87', '470377.91', '509024.04', '452445.75', '472652.43', '447792.20',
        #              '487601.29', '458804.70', '469694.46', '527154.22', '473446.19', '533971.78',
        #              '522563.08', '477644.82', '529917.88'],
        #     'items': ['156716', '166091', '157314', '161014', '163154',
        #               '159885', '147613', '169566', '152841', '162649', '166242',
        #               '162658', '166178', '170624', '160004', '166241', '173345',
        #               '161079', '160936', '176689', '164710', '182093', '168806',
        #               '174165', '181973', '169591', '182203', '180718', '179392',
        #               '182246', '165246', '178925', '180831', '190621', '174492',
        #               '191248', '188894', '180072', '191683', '183785', '189053',
        #               '189574', '169575', '182839', '182354', '189585', '179204',
        #               '193802', '181322', '185098', '194089', '173789', '195856',
        #               '182289', '167349', '185008']
        # }
        # for i, row in enumerate(all_rows):
        #     self.assertEqual(row['actual_cost'], expected['cost'][i])
        #     self.assertEqual(row['items'], expected['items'][i])

    def test_chemical_by_all(self):
        pass

    def test_bnf_section_by_all(self):
        pass


class TestSmokeTestSpendingByOnePractice(SmokeTestBase):

    def test_presentation_by_one_practice(self):
        url = '%s/api/1.0/spending_by_practice/?format=csv&' % self.DOMAIN
        url += 'code=0703021Q0BBAAAA&org=A81015'  # Cerazette 75mcg.
        r = requests.get(url)
        f = StringIO.StringIO(r.text)
        reader = csv.DictReader(f)
        all_rows = []
        for row in reader:
            all_rows.append(row)

        self.assertEqual(len(all_rows), self.NUM_RESULTS)

        expected = {
            'cost': ['138.94', '128.23', '77.57', '42.82', '117.64',
                     '248.45', '90.93', '173.86', '101.58', '123.08', '120.4',
                     '145.92', '197.85', '272.74', '90.98', '69.68', '206.22',
                     '109.75', '144.75', '144.8', '139.13', '166.1', '115.02',
                     '145.13', '190.37', '112.42', '198.47', '114.5', '216.49',
                     '230.51', '158.4', '153.23', '118.48', '175.15', '136.83',
                     '166.24', '110.15', '147.84', '166.75', '139.35', '191.03',
                     '145.36', '94.09', '190.16', '118.21', '126.32', '163.56',
                     '150.81', '138.92', '153.6', '103.61', '62.03', '165.33',
                     '106.48', '99.87', '117.65', '100.59', '89.03', '112.21',
                     '94.8'],
            'items': ['16', '14', '12', '7', '13',
                      '24', '9', '17', '12', '12', '14',
                      '21', '18', '26', '12', '12', '19',
                      '10', '17', '18', '16', '16', '13',
                      '18', '20', '11', '20', '17', '22',
                      '20', '17', '16', '14', '15', '15',
                      '15', '12', '17', '19', '14', '18',
                      '17', '11', '20', '14', '13', '14',
                      '16', '13', '12', '10', '6', '14',
                      '11', '9', '10', '9', '10', '8',
                      '10']
        }

        for i, row in enumerate(all_rows):
            self.assertEqual(row['actual_cost'], expected['cost'][i])
            self.assertEqual(row['items'], expected['items'][i])

    def test_chemical_by_one_practice(self):
        url = '%s/api/1.0/spending_by_practice/?' % self.DOMAIN
        url += 'format=csv&code=0212000AA&org=A81015'  # Rosuvastatin Calcium.
        r = requests.get(url)
        f = StringIO.StringIO(r.text)
        reader = csv.DictReader(f)
        all_rows = []
        for row in reader:
            all_rows.append(row)

        self.assertEqual(len(all_rows), self.NUM_RESULTS)

        expected = {
            'cost': ['57.22', '90.47', '57.21', '49.89', '49.92',
                     '16.63', '73.96', '57.31', '57.24', '57.32', '73.94',
                     '33.28', '90.58', '49.94', '90.56', '49.94', '81.44',
                     '33.32', '33.35',  '57.41', '57.3', '40.73', '57.28',
                     '57.38', '57.31', '56.16',  '57.29', '49.89', '83.18',
                     '98.07', '57.39', '81.5', '64.74', '97.99', '57.29',
                     '98.02', '81.38', '105.44', '57.39', '105.32', '64.72',
                     '98.06', '98.02', '98.18', '98.06', '64.8', '81.4',
                     '57.45', '81.46', '105.57', '16.68', '81.3', '125.55',
                     '84.75', '84.93', '109.11', '84.91', '109.01', '84.96',
                     '108.99'],
            'items': ['3', '5', '3', '3', '3',
                      '1', '4', '3', '3', '3', '4',
                      '2', '5', '3', '5', '3', '4',
                      '2', '2', '3', '3', '2', '3',
                      '3', '3', '3', '3', '3', '5',
                      '5', '3', '4', '3', '5', '3',
                      '5', '4', '5', '3', '5', '3',
                      '5', '5', '5', '5', '3', '4',
                      '3', '4', '5', '1', '4', '6',
                      '4', '4', '5', '4', '5', '4',
                      '5']
        }
        for i, row in enumerate(all_rows):
            self.assertEqual(row['actual_cost'], expected['cost'][i])
            self.assertEqual(row['items'], expected['items'][i])

    def test_multiple_chemicals_by_one_practice(self):
        url = '%s/api/1.0/spending_by_practice/?format=csv&' % self.DOMAIN
        url += 'code=0212000B0,0212000C0,0212000M0,0212000X0,0212000Y0'
        url += '&org=C85020'  # Multiple generic statins.
        r = requests.get(url)
        f = StringIO.StringIO(r.text)
        reader = csv.DictReader(f)
        all_rows = []
        for row in reader:
            all_rows.append(row)

        self.assertEqual(len(all_rows), self.NUM_RESULTS)

        expected = {
            'cost': ['9979.53', '10289.65', '9675.42', '10249.11', '10835.87',
                     '9721.39', '9255.99', '10763.7', '9363.32', '10079.41', '10457.78',
                     '10186.81', '10481.81', '10658.54', '9891.32', '11073.95', '10959.99',
                     '9550.1', '10305.12', '11385.31', '9820.74', '12811.91', '4283.13',
                     '4285.25', '2804.97', '2808.93', '2513.38', '2511.02', '2461.4',
                     '2422.92', '2225.54', '2243.14', '2458.26', '2648.84', '2269.74',
                     '2411.39', '2428.54', '2230.12', '2335.49', '2115.65', '2425.06',
                     '2274.16', '2207.01', '2322.6', '2043.0', '2059.34', '1973.39',
                     '2256.22', '2040.32', '2054.39', '2316.73', '2342.52', '2042.44',
                     '2286.73', '2527.1', '2378.36', '2273.38', '2267.96', '2316.11',
                     '2499.35'],
            'items': ['1367', '1428', '1375', '1398', '1573',
                      '1316', '1260', '1527', '1343', '1366', '1468',
                      '1381', '1511', '1491', '1394', '1561', '1555',
                      '1454', '1530', '1601', '1459', '1895', '1788',
                      '1854', '1931', '1772', '1949', '1867', '1917',
                      '1901', '1759', '1813', '1886', '2002', '1742',
                      '1897', '1883', '1777', '1977', '1830', '2068',
                      '1945', '1812', '1826', '1871', '1867', '1809',
                      '2030', '1813', '1837', '1893', '1906', '1725',
                      '1908', '2028', '1992', '1938', '1869', '1967',
                      '2177']
        }
        for i, row in enumerate(all_rows):
            self.assertEqual(row['actual_cost'], expected['cost'][i])
            self.assertEqual(row['items'], expected['items'][i])

    def test_bnf_section_by_one_practice(self):
        url = '%s/api/1.0/spending_by_practice/?format=csv&code=0304&org=L84077' % self.DOMAIN
        r = requests.get(url)  # BNF section 3.4: Antihistamines etc.
        f = StringIO.StringIO(r.text)
        reader = csv.DictReader(f)
        all_rows = []
        for row in reader:
            all_rows.append(row)

        self.assertEqual(len(all_rows), self.NUM_RESULTS)

        expected = {
            'cost': ['103.89', '121.07', '257.2', '74.6', '112.71',
                     '99.62', '78.03', '219.45', '104.22', '130.93', '242.17',
                     '150.92', '261.08', '103.75', '48.54', '85.68', '70.13',
                     '105.4', '39.12', '122.96', '177.47', '110.2', '213.01',
                     '317.37', '180.87', '178.11', '97.58', '170.66', '200.57',
                     '77.88', '45.8', '153.94', '91.94', '178.93', '196.83',
                     '257.21', '194.35', '107.01', '304.33', '115.41', '76.98',
                     '136.66', '121.89', '85.19', '201.19', '148.67', '238.95',
                     '185.69', '152.56', '202.67', '166.08', '156.27', '82.07',
                     '69.95', '75.88', '123.5', '172.32', '166.42', '247.19',
                     '345.6'],
            'items': ['37', '33', '35', '37', '36',
                      '35', '30', '50', '59', '57', '70',
                      '52', '49', '41', '20', '30', '25',
                      '28', '19', '42', '54', '66', '59',
                      '68', '50', '46', '40', '44', '45',
                      '43', '34', '46', '46', '76', '68',
                      '84', '62', '38', '55', '49', '50',
                      '59', '54', '55', '73', '73', '94',
                      '98', '73', '63', '68', '54', '60',
                      '60', '62', '60', '73', '70', '93',
                      '103']
        }
        for i, row in enumerate(all_rows):
            self.assertEqual(row['actual_cost'], expected['cost'][i])
            self.assertEqual(row['items'], expected['items'][i])


class TestSmokeTestSpendingByCCG(unittest.TestCase):

    def test_presentation_by_one_ccg(self):
        pass
        # url = '%s/api/1.0/spending_by_ccg?' % self.DOMAIN
        # url += 'code=0403030E0AAAAAA&org=10Q'

    def test_chemical_by_one_ccg(self):
        pass
        # url = '%s/api/1.0/spending_by_ccg?code=0212000AA&org=10Q' % self.DOMAIN

    def test_bnf_section_by_one_ccg(self):
        pass
        # url = '%s/api/1.0/spending_by_ccg' % self.DOMAIN
        # url += '?code=0801&org=11M'  # BNF section 8.1: Cytoxic drugs.

if __name__ == '__main__':
    unittest.main()
