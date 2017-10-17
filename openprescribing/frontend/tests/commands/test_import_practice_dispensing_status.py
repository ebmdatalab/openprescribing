from django.core.management import call_command
from django.test import TestCase
from frontend.models import Practice


def setUpModule():
    Practice.objects.create(code='1', name='ADDINGHAM SURGERY',
                            postcode='LS29 0LZ')
    Practice.objects.create(code='2', name='HAWORTH MEDICAL PRACTICE',
                            postcode='BD22 8DH')
    Practice.objects.create(code='3', name='TOWNHEAD SURGERY',
                            postcode='BD24 9JA')
    Practice.objects.create(code='4', name='CHARING SURGERY',
                            postcode='TN27 0AW')
    Practice.objects.create(code='B82005', name='PRIORY MEDICAL GROUP',
                            postcode='YO24 3WX')


def tearDownModule():
    call_command('flush', verbosity=0, interactive=False)


class CommandsTestCase(TestCase):

    def test_import_practice_dispensing_status(self):
        args = []
        fname = 'frontend/tests/fixtures/commands/'
        fname += 'dispensing_practices-sample.xls'
        opts = {
            'filename': fname,
            'date': '2015-01-31'
        }
        call_command('import_practice_dispensing_status', *args, **opts)

        practice = Practice.objects.get(code='1')
        pid = practice.practiceisdispensing_set.filter(date='2015-01-31')
        self.assertEqual(pid.count(), 1)
        practice = Practice.objects.get(code='2')
        pid = practice.practiceisdispensing_set.filter(date='2015-01-31')
        self.assertEqual(pid.count(), 1)
        practice = Practice.objects.get(code='B82005')
        pid = practice.practiceisdispensing_set.filter(date='2015-01-31')
        self.assertEqual(pid.count(), 0)
