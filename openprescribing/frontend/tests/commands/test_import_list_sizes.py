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
    def test_error_for_missing_list_data(self):
        """Supplied patient list size data must always cover any existing gaps
        in previously-imported list size data.

        """
        args = []
        fname = 'frontend/tests/fixtures/commands/'
        fname += 'patient_list_size/2040_05/Patient_List_Size_2013_10-12.csv'
        opts = {
            'filename': fname,
            'verbosity': 0
        }
        # Now check that we get an error (because there is now a gap)
        with self.assertRaises(CommandError):
            call_command('import_list_sizes', *args, **opts)

    def test_import_bsa_multiple_list_size(self):
        fname = ("frontend/tests/fixtures/commands/patient_list_size/"
                 "%s/Patient_List_Size_2013_10-12.csv")
        args = [fname % '2040_02', fname % '2040_05']
        opts = {}
        call_command('import_list_sizes', *args, **opts)
        list_sizes = PracticeStatistics.objects.all()
        self.assertEqual(len(list_sizes), 6)
        self.assertEqual(str(list_sizes[5].date), '2040-03-01')
        last_log = ImportLog.objects.latest_in_category('patient_list_size')
        self.assertEqual(
            last_log.current_at.strftime('%Y-%m-%d'),
            PRESCRIBING_DATE)

    def test_import_bsa_list_size_quarterly(self):
        args = []
        fname = 'frontend/tests/fixtures/commands/'
        fname += 'patient_list_size/2040_02/Patient_List_Size_2013_10-12.csv'
        opts = {
            'filename': fname
        }
        call_command('import_list_sizes', *args, **opts)
        last_list_size_date = '2040-02-01'
        list_sizes = PracticeStatistics.objects.all()

        self.assertEqual(len(list_sizes), 4)

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


class MissingMonthsTestCase(TestCase):
    """In order to track which months of patient list data are required,
    we store last-imported dates for both lists. These tests check
    that the missing months returned by the method in question are correct.

    """
    def test_imported_list_sizes_are_up_to_date_with_prescribing_data(self):
        ImportLog.objects.create(
            current_at='2050-01-01',
            category='patient_list_size'
        )
        ImportLog.objects.create(
            current_at='2050-01-01',
            category='prescribing'
        )
        self.assertEqual(
            Command().months_with_prescribing_data_but_no_list_data(), [])

    def test_imported_list_sizes_are_behind_prescribing_data(self):
        ImportLog.objects.create(
            current_at='2050-01-01',
            category='patient_list_size'
        )
        ImportLog.objects.create(
            current_at='2050-03-01',
            category='prescribing'
        )

        self.assertEqual(
            Command().months_with_prescribing_data_but_no_list_data(),
            ['2050-02-01', '2050-03-01'])

    def test_imported_list_sizes_are_ahead_of_prescribing_data(self):
        ImportLog.objects.create(
            current_at='2050-04-01',
            category='patient_list_size'
        )
        ImportLog.objects.create(
            current_at='2050-03-01',
            category='prescribing'
        )
        self.assertEqual(
            Command().months_with_prescribing_data_but_no_list_data(),
            [])
