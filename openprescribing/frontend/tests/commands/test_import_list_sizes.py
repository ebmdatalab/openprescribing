from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase
from frontend.models import Practice, PracticeStatistics, ImportLog
from frontend.management.commands.import_list_sizes import Command

PRESCRIBING_DATE = '2040-03-01'


def setUpModule():
    Practice.objects.create(code='N84014',
                            name='AINSDALE VILLAGE SURGERY')
    Practice.objects.create(code='P84034',
                            name='BARLOW MEDICAL CENTRE')
    Practice.objects.create(code='Y02229',
                            name='ADDACTION NUNEATON')
    ImportLog.objects.create(
        current_at='2039-12-01',
        category='patient_list_size'
    )
    ImportLog.objects.create(
        current_at=PRESCRIBING_DATE,
        category='prescribing'
    )


def tearDownModule():
    call_command('flush', verbosity=0, interactive=False)


class CommandsTestCase(TestCase):
    def test_import_list_sizes(self):
        fname = 'frontend/tests/fixtures/commands/'
        fname += 'patient_list_size/2040_02/patient_list_size_new.csv'
        call_command('import_list_sizes', '--filename={}'.format(fname))
        last_list_size_date = '2040-02-01'
        list_sizes = PracticeStatistics.objects.all()

        self.assertEqual(len(list_sizes), 2)

        p = PracticeStatistics.objects.get(practice_id='N84014',
                                           date=last_list_size_date)
        self.assertEqual(p.total_list_size, 40)
        self.assertEqual(p.astro_pu_cost, 199.419458446917)
        self.assertEqual(p.astro_pu_items, 780.191218783541)
        self.assertEqual('%.3f' % p.star_pu['oral_antibacterials_item'],
                         '27.135')
        self.assertEqual('%.3f' % p.star_pu['cox-2_inhibitors_cost'],
                         '13.050')
        self.assertEqual('%.3f' % p.star_pu['antidepressants_adq'],
                         '887.100')
        for k in p.star_pu:
            self.assertNotEqual(p.star_pu[k], 0)
            self.assertNotEqual(p.star_pu[k], None)
