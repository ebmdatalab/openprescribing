import datetime
import unittest

from mock import patch

from django.core.management import call_command
from django.db import InternalError
from django.test import TestCase

from common import utils
from frontend.management.commands.import_hscic_prescribing import Command
from frontend.models import Chemical
from frontend.models import ImportLog
from frontend.models import PCT
from frontend.models import Practice
from frontend.models import PracticeStatistics
from frontend.models import Prescription
from frontend.models import Section


# Number of bytes to send/receive in each request.
CHUNKSIZE = 2 * 1024 * 1024

# Mimetype to use if one can't be guessed from the file extension.
DEFAULT_MIMETYPE = 'application/octet-stream'


class UnitTests(unittest.TestCase):
    @patch('django.db.connection.cursor')
    def test_create_partition_december(self, mock_cursor):
        date = datetime.date(2011, 12, 1)
        cmd = Command()
        cmd.date = date
        cmd.create_partition()
        mock_execute = mock_cursor.return_value.__enter__.return_value.execute
        execute_args = mock_execute.call_args[0][0]
        self.assertIn(
            "processing_date >= DATE '2011-12-01'", execute_args)
        self.assertIn(
            "processing_date < DATE '2012-01-01'", execute_args)

    def test_date_from_filename(self):
        cmd = Command()
        old_style = cmd._date_from_filename(
            'something/T201304PDPI+BNFT_formatted.CSV')
        self.assertEqual(old_style, datetime.date(2013, 4, 1))
        new_style = cmd._date_from_filename(
            'something/2013_04/formatted.CSV')
        self.assertEqual(new_style, datetime.date(2013, 4, 1))


class ImportTestCase(TestCase):
    """Tests we can import data from a local flat file

    """
    def setUp(self):
        self.chemical = Chemical.objects.create(
            bnf_code='0401020K0', chem_name='test')
        self.practice = Practice.objects.create(code='Y03375', name='test')
        self.pct = PCT.objects.create(code='5D7', name='test')
        Chemical.objects.create(bnf_code='0410030C0', chem_name='test')
        Practice.objects.create(code='Y00135', name='test')
        p = Practice.objects.create(code='Y01957', name='test')
        Section.objects.create(bnf_id='0401', bnf_chapter=4, is_current=False)
        Section.objects.create(bnf_id='0909', bnf_chapter=9, is_current=False)
        PracticeStatistics.objects.create(
            practice=p,
            date='2001-01-01',
            male_0_4=1,
            female_0_4=1,
            male_5_14=1,
            female_5_14=1,
            male_15_24=1,
            female_15_24=1,
            male_25_34=1,
            female_25_34=1,
            male_35_44=1,
            female_35_44=1,
            male_45_54=1,
            female_45_54=1,
            male_55_64=1,
            female_55_64=1,
            male_65_74=1,
            female_65_74=1,
            male_75_plus=1,
            female_75_plus=1,
            total_list_size=28,
            astro_pu_cost=205.7,
            astro_pu_items=400.2)

        test_file = 'frontend/tests/fixtures/commands/'
        test_file += 'T201304PDPI+BNFT_formatted.CSV'
        self.new_opts = {
            'filename': test_file
        }
        db_name = 'test_' + utils.get_env_setting('DB_NAME')
        self.env = patch.dict(
            'os.environ', {'DB_NAME': db_name})
        with self.env:
            call_command('import_hscic_prescribing', **self.new_opts)

    def test_import_drops_existing(self):
        with self.env:
            call_command('import_hscic_prescribing', **self.new_opts)
        self.assertEqual(Prescription.objects.count(), 15)
        self.assertEqual(PracticeStatistics.objects.count(), 0)

    def test_inserts_fail(self):
        with self.assertRaises(InternalError):
            Prescription.objects.create(
                pct=self.pct, practice=self.practice,
                presentation_code='0000',
                total_items=4,
                actual_cost=4, quantity=4,
                processing_date='2013-04-01')

    def test_import_creates_missing_entities(self):
        pcts = PCT.objects.all()
        self.assertEqual(pcts.count(), 2)
        self.assertEqual(len(Practice.objects.all()), 4)

    def test_import_creates_prescriptions(self):
        prescriptions = Prescription.objects.all()
        self.assertEqual(prescriptions.count(), 15)

        p = Prescription.objects.filter(presentation_code='0401020K0AAAIAI')
        self.assertEqual(p.count(), 3)

        p = Prescription.objects.get(presentation_code='0410030C0AAAFAF')
        self.assertEqual(p.pct.code, '5D7')
        self.assertEqual(p.practice.code, 'Y01957')
        self.assertEqual(p.total_items, 1346)
        self.assertEqual(p.actual_cost, 11270.33)
        self.assertEqual(p.quantity, 878870)
        self.assertEqual(p.processing_date, datetime.date(2013, 4, 1))
        l = ImportLog.objects.latest_in_category('prescribing')
        self.assertEqual(l.current_at.strftime('%Y-%m-%d'), '2013-04-01')

    def test_mark_as_current(self):
        self.assertFalse(Section.objects.get(bnf_id='0909').is_current)
        self.assertTrue(Section.objects.get(bnf_id='0401').is_current)
