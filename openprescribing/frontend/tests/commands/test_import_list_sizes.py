from django.core.management import call_command
from django.test import TestCase
from frontend.models import PracticeList, Practice


def setUpModule():
        Practice.objects.create(code='N84014',
                                name='AINSDALE VILLAGE SURGERY')
        Practice.objects.create(code='P84034',
                                name='BARLOW MEDICAL CENTRE')
        Practice.objects.create(code='Y02229',
                                name='ADDACTION NUNEATON')


def tearDownModule():
    call_command('flush', verbosity=0, interactive=False)


class CommandsTestCase(TestCase):
    def test_import_bnf_codes(self):

        args = []
        fname = 'frontend/tests/fixtures/commands/'
        fname += 'Patient_List_Size_2013_10-12.csv'
        opts = {
            'filename': fname
        }
        call_command('import_list_sizes', *args, **opts)

        list_sizes = PracticeList.objects.all()
        self.assertEqual(len(list_sizes), 9)

        p = PracticeList.objects.get(practice_id='N84014',
                                     date='2013-10-01')
        self.assertEqual(p.total_list_size, 2932)
        self.assertEqual(p.astro_pu_cost, 12318.9)
        self.assertEqual(p.astro_pu_items, 45350.1)
        self.assertEqual('%.3f' % p.star_pu['oral_antibacterials_item'],
                         '1764.245')
        self.assertEqual('%.3f' % p.star_pu['cox-2_inhibitors_cost'],
                         '968.672')
        self.assertEqual('%.3f' % p.star_pu['antidepressants_adq'],
                         '66516.700')
        for k in p.star_pu:
            self.assertNotEqual(p.star_pu[k], 0)
            self.assertNotEqual(p.star_pu[k], None)

        # Test that our script creates all months in the quarter.
        p = PracticeList.objects.get(practice_id='N84014',
                                     date='2013-11-01')
        self.assertEqual(p.total_list_size, 2932)
        self.assertEqual(p.astro_pu_cost, 12318.9)
        self.assertEqual(p.astro_pu_items, 45350.1)
        self.assertEqual('%.3f' % p.star_pu['oral_antibacterials_item'],
                         '1764.245')
        self.assertEqual('%.3f' % p.star_pu['cox-2_inhibitors_cost'],
                         '968.672')
        self.assertEqual('%.3f' % p.star_pu['antidepressants_adq'],
                         '66516.700')

        p = PracticeList.objects.get(practice_id='N84014',
                                     date='2013-12-01')
        self.assertEqual(p.total_list_size, 2932)
        self.assertEqual(p.astro_pu_cost, 12318.9)
        self.assertEqual(p.astro_pu_items, 45350.1)
        self.assertEqual('%.3f' % p.star_pu['oral_antibacterials_item'],
                         '1764.245')
        self.assertEqual('%.3f' % p.star_pu['cox-2_inhibitors_cost'],
                         '968.672')
        self.assertEqual('%.3f' % p.star_pu['antidepressants_adq'],
                         '66516.700')

        p = PracticeList.objects.get(practice_id='P84034',
                                     date='2013-12-01')
        self.assertEqual(p.total_list_size, 13439)
        self.assertEqual(p.astro_pu_cost, 41202.3)
        self.assertEqual(p.astro_pu_items, 143921.9)
        self.assertEqual('%.3f' % p.star_pu['oral_antibacterials_item'],
                         '7100.005')
        self.assertEqual('%.3f' % p.star_pu['cox-2_inhibitors_cost'],
                         '3287.111')
        self.assertEqual('%.3f' % p.star_pu['antidepressants_adq'],
                         '295093.300')

        p = PracticeList.objects.get(practice_id='Y02229',
                                     date='2013-12-01')
        self.assertEqual(p.total_list_size, 0)
        self.assertEqual(p.astro_pu_cost, 0)
        self.assertEqual(p.astro_pu_items, 0)
        self.assertEqual(p.star_pu['oral_antibacterials_item'], 0)
        self.assertEqual(p.star_pu['cox-2_inhibitors_cost'], 0)
        self.assertEqual(p.star_pu['antidepressants_adq'], 0)
