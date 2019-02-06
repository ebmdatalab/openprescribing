from django.test import SimpleTestCase

from matrixstore.dates import generate_dates


class TestDates(SimpleTestCase):

    def test_generate_dates(self):
        results = generate_dates('2019-02', 15)
        expected = [
            '2017-12-01', '2018-01-01', '2018-02-01', '2018-03-01',
            '2018-04-01', '2018-05-01', '2018-06-01', '2018-07-01',
            '2018-08-01', '2018-09-01', '2018-10-01', '2018-11-01',
            '2018-12-01', '2019-01-01', '2019-02-01'
        ]
        self.assertEqual(results, expected)
